# -*- coding: utf-8 -*-
#
####################################################
#
# PRISM - Pipeline for animation and VFX projects
#
# www.prism-pipeline.com
#
# contact: contact@prism-pipeline.com
#
####################################################
#
#
# Copyright (C) 2016-2020 Richard Frangenberg
#
# Licensed under GNU GPL-3.0-or-later
#
# This file is part of Prism.
#
# Prism is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Prism is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Prism.  If not, see <https://www.gnu.org/licenses/>.


import logging

try:
    from PySide2.QtCore import *
    from PySide2.QtGui import *
    from PySide2.QtWidgets import *
except:
    from PySide.QtCore import *
    from PySide.QtGui import *

from PrismUtils.Decorators import err_catcher as err_catcher

import hou

logger = logging.getLogger(__name__)


class Prism_Houdini_Filecache(object):
    def __init__(self, plugin):
        self.plugin = plugin
        self.core = self.plugin.core
        self.initState = None
        self.executeBackground = False
        self.nodeExecuted = False
        self.stateType = "Export"
        self.listType = "Export"

    @err_catcher(name=__name__)
    def getTypeName(self):
        return "prism::Filecache"

    @err_catcher(name=__name__)
    def getFormats(self):
        blacklisted = [".hda", "ShotCam", "other", ".rs"]
        appFormats = self.core.appPlugin.outputFormats
        nodeFormats = [f for f in appFormats if f not in blacklisted]
        bgsc = nodeFormats.pop(1)
        nodeFormats.insert(0, bgsc)

        tokens = []
        for f in nodeFormats:
            tokens.append(f)
            tokens.append(f)

        return tokens

    @err_catcher(name=__name__)
    def getLocations(self, kwargs):
        # if function gets called before scene is fully loaded
        sm = self.core.getStateManager(create=False)
        if not sm or self.core.getCurrentFileName() != sm.scenename:
            return []

        if self.initState:
            state = self.initState
        else:
            state = self.getStateFromNode(kwargs)

        cb = state.ui.cb_outPath
        locations = [cb.itemText(idx) for idx in range(cb.count())]

        tokens = []
        for loc in locations:
            tokens.append(loc)
            tokens.append(loc)

        return tokens

    @err_catcher(name=__name__)
    def getReadVersions(self, kwargs):
        versions = []
        versions.insert(0, "latest")

        tokens = []
        for v in versions:
            tokens.append(v)
            tokens.append(v)

        return tokens

    @err_catcher(name=__name__)
    def getSaveVersions(self, kwargs):
        versions = []
        versions.insert(0, "next")

        tokens = []
        for v in versions:
            tokens.append(v)
            tokens.append(v)

        return tokens

    @err_catcher(name=__name__)
    def onNodeCreated(self, kwargs):
        self.plugin.onNodeCreated(kwargs)
        kwargs["node"].setColor(hou.Color(0.95, 0.5, 0.05))
        self.getStateFromNode(kwargs)

    @err_catcher(name=__name__)
    def nodeInit(self, node, state=None):
        if not state:
            state = self.getStateFromNode({"node": node})

        self.initState = state
        location = node.parm("format").evalAsString()
        task = node.parm("task").eval()
        outformat = node.parm("format").evalAsString()
        location = node.parm("location").evalAsString()
        state.ui.setTaskname(task)
        state.ui.setRangeType("Node")
        state.ui.setOutputType(outformat)
        state.ui.setLocation(location)
        self.updateLatestVersion(node)
        self.initState = None

    @err_catcher(name=__name__)
    def onNodeDeleted(self, kwargs):
        self.plugin.onNodeDeleted(kwargs)

    @err_catcher(name=__name__)
    def getStateFromNode(self, kwargs):
        return self.plugin.getStateFromNode(kwargs)

    @err_catcher(name=__name__)
    def setTaskFromNode(self, kwargs):
        taskname = kwargs["node"].parm("task").eval()
        state = self.getStateFromNode(kwargs)
        state.ui.setTaskname(taskname)
        self.updateLatestVersion(kwargs["node"])

    @err_catcher(name=__name__)
    def setFormatFromNode(self, kwargs):
        state = self.getStateFromNode(kwargs)
        state.ui.setOutputType(kwargs["script_value"])

    @err_catcher(name=__name__)
    def setLocationFromNode(self, kwargs):
        location = kwargs["node"].parm("location").evalAsString()
        state = self.getStateFromNode(kwargs)
        state.ui.setLocation(location)

    @err_catcher(name=__name__)
    def showInStateManagerFromNode(self, kwargs):
        self.plugin.showInStateManagerFromNode(kwargs)

    @err_catcher(name=__name__)
    def openInExplorerFromNode(self, kwargs):
        state = self.getStateFromNode(kwargs)
        folderpath = state.ui.l_pathLast.text()
        self.core.openFolder(folderpath)

    @err_catcher(name=__name__)
    def refreshNodeUi(self, node, state):
        taskname = state.getTaskname()
        if taskname != node.parm("task").eval():
            self.plugin.setNodeParm(node, "task", taskname, clear=True)

        rangeType = state.getRangeType()
        if rangeType != "Node":
            startFrame, endFrame = state.getFrameRange(rangeType)
            if endFrame is None:
                endFrame = startFrame

            if startFrame != node.parm("f1").eval():
                self.plugin.setNodeParm(node, "f1", startFrame, clear=True)

            if endFrame != node.parm("f2").eval():
                self.plugin.setNodeParm(node, "f2", endFrame, clear=True)

        outType = state.getOutputType()
        if outType != node.parm("format").evalAsString():
            self.plugin.setNodeParm(node, "format", outType, clear=True)

    @err_catcher(name=__name__)
    def executeNode(self, node):
        if node.parm("format").evalAsString() == ".abc":
            ropName = "write_alembic"
        else:
            ropName = "write_geo"

        if self.executeBackground:
            parmName = "executebackground"
        else:
            parmName = "execute"

        rop = node.node(ropName)
        rop.parm(parmName).pressButton()
        QCoreApplication.processEvents()
        self.updateLatestVersion(node)
        node.node("switch_abc").cook(force=True)
        if not self.executeBackground and node.parm("showSuccessPopup").eval() and self.nodeExecuted:
            self.core.popup("Finished caching successfully.", severity="info", modal=False)

        if self.executeBackground:
            return "background"
        else:
            return True

    @err_catcher(name=__name__)
    def executePressed(self, kwargs, background=False):
        if not kwargs["node"].inputs():
            self.core.popup("No inputs connected")
            return

        sm = self.core.getStateManager()
        state = self.getStateFromNode(kwargs)
        sanityChecks = bool(kwargs["node"].parm("sanityChecks").eval())
        version = self.getWriteVersionFromNode(kwargs["node"])
        saveScene = bool(kwargs["node"].parm("saveScene").eval())
        incrementScene = saveScene and bool(kwargs["node"].parm("incrementScene").eval())

        self.nodeExecuted = True
        self.executeBackground = background
        sm.publish(
            executeState=True,
            useVersion=version,
            states=[state],
            successPopup=False,
            saveScene=saveScene,
            incrementScene=incrementScene,
            sanityChecks=sanityChecks,
            versionWarning=False,
        )
        self.executeBackground = False
        self.nodeExecuted = False
        self.reload(kwargs)

    @err_catcher(name=__name__)
    def nextChanged(self, kwargs):
        self.updateLatestVersion(kwargs["node"])

    @err_catcher(name=__name__)
    def latestChanged(self, kwargs):
        self.updateLatestVersion(kwargs["node"])

    @err_catcher(name=__name__)
    def getReadVersionFromNode(self, node):
        if node.parm("latestVersionRead").eval():
            version = "latest"
        else:
            version = node.parm("readVersion").evalAsString()

        return version

    @err_catcher(name=__name__)
    def getWriteVersionFromNode(self, node):
        if node.parm("nextVersionWrite").eval():
            version = "next"
        else:
            version = node.parm("writeVersion").evalAsString()

        return version

    @err_catcher(name=__name__)
    def updateLatestVersion(self, node):
        latestVersion = None
        if node.parm("nextVersionWrite").eval():
            task = node.parm("task").eval()
            versionpath = self.core.products.getLatestVersionpathFromProduct(task)
            if not versionpath:
                latestVersion = 0
            else:
                latestVersion = self.core.products.getVersionFromFilepath(versionpath, num=True)
            node.parm("writeVersion").set(latestVersion + 1)

        if node.parm("latestVersionRead").eval():
            if latestVersion is None:
                task = node.parm("task").eval()
                versionpath = self.core.products.getLatestVersionpathFromProduct(task)
                if not versionpath:
                    latestVersion = 0
                else:
                    latestVersion = self.core.products.getVersionFromFilepath(versionpath, num=True)
            node.parm("readVersion").set(latestVersion)

    @err_catcher(name=__name__)
    def getParentFolder(self, create=True, node=None):
        sm = self.core.getStateManager()
        for state in sm.states:
            if state.ui.listType != "Export" or state.ui.className != "Folder":
                continue

            if state.ui.e_name.text() != "Filecaches":
                continue

            return state

        if create:
            stateData = {
                "statename": "Filecaches",
                "listtype": "Export",
                "stateenabled": "PySide2.QtCore.Qt.CheckState.Checked",
                "stateexpanded": True,
            }
            state = sm.createState("Folder", stateData=stateData)
            return state

    @err_catcher(name=__name__)
    def findExistingVersion(self, kwargs, mode):
        import TaskSelection

        ts = TaskSelection.TaskSelection(core=self.core)

        product = kwargs["node"].parm("task").eval()
        filepath = self.core.getCurrentFileName()
        data = self.core.getScenefileData(filepath)
        result = ts.navigateToProduct(product, entity=data["entity"], entityName=data["fullEntityName"])
        widget = ts.tw_versions
        if not result or not widget.rowCount():
            self.core.popup("No versions exist in the current context.")
            return

        if mode == "write":
            usevparm = kwargs["node"].parm("nextVersionWrite")
            vparm = kwargs["node"].parm("writeVersion")
        elif mode == "read":
            usevparm = kwargs["node"].parm("latestVersionRead")
            vparm = kwargs["node"].parm("readVersion")

        if not usevparm.eval():
            versionName = self.core.versionFormat % vparm.eval()
            ts.navigateToVersion(versionName)

        self.core.parentWindow(widget)
        widget.setWindowTitle("Select Version")
        widget.resize(1000, 600)

        ts.productPathSet.connect(lambda x, m=mode, k=kwargs: self.versionSelected(x, m, k))
        ts.productPathSet.connect(widget.close)

        widget.show()

    @err_catcher(name=__name__)
    def versionSelected(self, path, mode, kwargs):
        if not path:
            return

        version = self.core.products.getVersionFromFilepath(path, num=True)

        if mode == "write":
            kwargs["node"].parm("nextVersionWrite").set(0)
            kwargs["node"].parm("writeVersion").set(version)
        elif mode == "read":
            kwargs["node"].parm("latestVersionRead").set(0)
            kwargs["node"].parm("readVersion").set(version)

        return version

    @err_catcher(name=__name__)
    def getProductName(self, node):
        return node.parm("task").eval()

    @err_catcher(name=__name__)
    def getImportPath(self):
        sm = self.core.getStateManager(create=False)
        if not sm or self.core.getCurrentFileName() != sm.scenename:
            return ""

        node = hou.pwd()
        product = self.getProductName(node)
        version = self.getReadVersionFromNode(node)
        if version == "latest":
            path = self.core.products.getLatestVersionpathFromProduct(product)
        else:
            path = self.core.products.getVersionpathFromProductVersion(product, version)

        if path:
            path = path.replace("\\", "/")
            path = self.core.appPlugin.detectCacheSequence(path)
            path = hou.expandString(path)
        else:
            path = ""

        return path

    @err_catcher(name=__name__)
    def getProductNames(self):
        names = []
        filepath = self.core.getCurrentFileName()
        data = self.core.getScenefileData(filepath)
        if data["entity"] == "invalid":
            return names
        names = self.core.products.getProductsFromEntity(data["entity"], data["fullEntityName"])
        names = sorted(names.keys())
        names = [name for name in names for _ in range(2)]
        return names

    @err_catcher(name=__name__)
    def reload(self, kwargs):
        isAbc = kwargs["node"].parm("switch_abc/input").eval()
        if isAbc:
            kwargs["node"].parm("read_alembic/reload").pressButton()
        else:
            kwargs["node"].parm("read_geo/reload").pressButton()

    @err_catcher(name=__name__)
    def getFrameranges(self):
        ranges = ["Save Current Frame", "Save Frame Range"]
        ranges = [r for r in ranges for _ in range(2)]
        return ranges

    @err_catcher(name=__name__)
    def getFrameRange(self, node):
        if node.parm("framerange").eval() == 0:
            startFrame = self.core.appPlugin.getCurrentFrame()
            endFrame = startFrame
        else:
            startFrame = node.parm("f1").eval()
            endFrame = node.parm("f2").eval()

        return startFrame, endFrame

    @err_catcher(name=__name__)
    def framerangeChanged(self, kwargs):
        state = self.getStateFromNode(kwargs)
        state.ui.updateUi()

    @err_catcher(name=__name__)
    def getNodeDescription(self):
        node = hou.pwd()
        version = self.getWriteVersionFromNode(node)
        if version == "next":
            version += " (%s)" % (self.core.versionFormat % node.parm("writeVersion").eval())
        descr = self.getProductName(node) + "\n" + version

        if not node.parm("latestVersionRead").eval():
            readv = self.core.versionFormat % node.parm("readVersion").eval()
            descr += "\nRead: " + readv

        return descr

    @err_catcher(name=__name__)
    def isSingleFrame(self, node):
        rangeType = node.parm("framerange").evalAsString()
        isSingle = rangeType == "Save Current Frame"
        return isSingle
