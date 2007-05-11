import wx
import wx.xrc as xrc
import random
from Tribler.vwxGUI.GuiUtility import GUIUtility
from Tribler.vwxGUI.tribler_topButton import tribler_topButton
from Tribler.CacheDB.CacheDBHandler import MyDBHandler
from Tribler.Dialogs.MugshotManager import MugshotManager
from Tribler.Dialogs.socnetmyinfo import MyInfoWizard
from Tribler.CacheDB.CacheDBHandler import MyPreferenceDBHandler

class ProfileOverviewPanel(wx.Panel):
    def __init__(self, *args, **kw):
#        print "<mluc> tribler_topButton in init"
        self.initDone = False
        self.elementsName = [ 'bgPanel_Overall', 'perf_Overall', 'icon_Overall', 'text_Overall', 
                             'bgPanel_Quality', 'perf_Quality', 'text_Quality', 
                             'bgPanel_Files', 'perf_Files', 'text_Files', 
                             'bgPanel_Persons', 'perf_Persons', 'text_Persons', 
                             'bgPanel_Download', 'perf_Download', 'text_Download', 
                             'bgPanel_Presence', 'perf_Presence', 'text_Presence',
                             'myNameField', 'thumb', 'edit']
        self.elements = {}
        self.data = {} #data related to profile information, to be used in details panel
        if len(args) == 0: 
            pre = wx.PrePanel() 
            # the Create step is done by XRC. 
            self.PostCreate(pre) 
            self.Bind(wx.EVT_WINDOW_CREATE, self.OnCreate) 
        else:
            wx.Panel.__init__(self, *args, **kw) 
            self._PostInit()     
        
    def OnCreate(self, event):
#        print "<mluc> tribler_topButton in OnCreate"
        self.Unbind(wx.EVT_WINDOW_CREATE)
        wx.CallAfter(self._PostInit)
        event.Skip()
        return True
    
    def _PostInit(self):
#        print "<mluc> tribler_topButton in _PostInit"
        # Do all init here
        self.guiUtility = GUIUtility.getInstance()
        self.utility = self.guiUtility.utility
        self.data_manager = self.guiUtility.standardOverview.data_manager
        self.mydb = MyPreferenceDBHandler()
#        self.Bind(wx.EVT_MOUSE_EVENTS, self.mouseAction)
#        self.Bind(wx.EVT_LEFT_UP, self.guiUtility.buttonClicked)
        for element in self.elementsName:
            xrcElement = xrc.XRCCTRL(self, element)
            if not xrcElement:
                print 'profileOverviewPanel: Error: Could not identify xrc element:',element
            self.elements[element] = xrcElement

        self.getNameMugshot()

        self.buttons = []
        #add mouse over text and progress icon
        for elem_name in self.elementsName:
            if elem_name.startswith("bgPanel_"):
                self.buttons.append(elem_name)
                but_elem = self.getGuiElement(elem_name)
                but_elem.setBackground(wx.Colour(203,203,203))
                suffix = elem_name[8:]
                text_elem = self.getGuiElement('text_%s' % suffix)
                perf_elem = self.getGuiElement('perf_%s' % suffix)
                icon_elem = self.getGuiElement('icon_%s' % suffix)
                if isinstance(self.getGuiElement(elem_name),tribler_topButton) :
                    if text_elem:
                        text_elem.Bind(wx.EVT_MOUSE_EVENTS, but_elem.mouseAction)
                    if perf_elem:
                        perf_elem.Bind(wx.EVT_MOUSE_EVENTS, but_elem.mouseAction)
                    if icon_elem:
                        icon_elem.Bind(wx. EVT_MOUSE_EVENTS, but_elem.mouseAction)
                else:
                    but_elem.Bind(wx.EVT_LEFT_UP, self.guiUtility.buttonClicked)
                if text_elem:
                    text_elem.Bind(wx.EVT_LEFT_UP, self.sendClick)
                if perf_elem:
                    perf_elem.Bind(wx.EVT_LEFT_UP, self.sendClick)
                if icon_elem:
                    icon_elem.Bind(wx.EVT_LEFT_UP, self.sendClick)
                    
        self.getGuiElement('myNameField').SetLabel('')

        self.initDone = True
        self.Refresh(True)
#        self.Update()
        self.timer = None
        wx.CallAfter(self.reloadData)

    def getNameMugshot(self):
        my_db = MyDBHandler()
        self.myname = my_db.get('name', '')
        mypermid = my_db.getMyPermid()
        mm = MugshotManager.getInstance()
        self.mugshot = mm.load_wxBitmap(mypermid)
        if self.mugshot is None:
            print "profileOverviewPanel: Bitmap for mypermid not found"
            self.mugshot = mm.get_default('personsMode','DEFAULT_THUMB')
        
    def showNameMugshot(self):
        self.getGuiElement('myNameField').SetLabel(self.myname)
        thumbpanel = self.getGuiElement('thumb')
        thumbpanel.setBitmap(self.mugshot)
        
    def sendClick(self, event):
        source = event.GetEventObject()
        source_name = source.GetName()
#        print "<mluc> send event from",source_name
        if source_name.startswith('text_') or source_name.startswith('perf_') or source_name.startswith('icon_'):
            #send event to background button
            but_name = 'bgPanel_'+source_name[5:]
            self.selectNewButton(but_name)
#            print "<mluc> send event to",but_name
            new_owner = self.getGuiElement(but_name)
            event.SetEventObject(new_owner)
            wx.PostEvent( new_owner, event)
        elif source_name.startswith('bgPanel_'):
            self.selectNewButton(source_name)
        elif source_name == "edit":
            self.OnMyInfoWizard(event)

    def selectNewButton(self, sel_but):
        for button in self.buttons:
            butElem = self.getGuiElement(button)
            if button == sel_but:
                if isinstance(butElem,tribler_topButton):
                    butElem.setSelected(True)
            elif isinstance(butElem, tribler_topButton) and butElem.isSelected():
                butElem.setSelected(False)

    def getGuiElement(self, name):
        if not self.elements.has_key(name) or not self.elements[name]:
#            print "[profileOverviewPanel] gui element %s not available" % name
            return None
        return self.elements[name]
    
    def reloadData(self, event=None):
        """updates the fields in the panel with new data if it has changed"""
        
        self.showNameMugshot()
        
        if not self.IsShown(): #should not update data if not shown
            return
        bShouldRefresh = False
        #set the overall ranking to a random number
#===============================================================================
#        new_index = random.randint(0,3) #used only for testing
#        elem = self.getGuiElement("icon_Overall")
#        if elem and new_index != elem.getIndex():
#            elem.setIndex(new_index)
#            bShouldRefresh = True
#===============================================================================
        overall_index = 0
        
        #get the number of downloads for this user
        count = len(self.mydb.getPrefList())
        #count = self.data_manager.getDownloadHistCount()
        aux_count = count
        if aux_count > 100:
            aux_count = 101
        if aux_count < 0:
            aux_count = 0
        new_index = int((aux_count-1)/25)+1 #from 0 to 5
        overall_index = overall_index + new_index*0.1667
#        print "<mluc> [after quality] overall=",overall_index
        qualityElem = self.getGuiElement("perf_Quality")    # Quality of tribler recommendation
        if qualityElem and new_index != qualityElem.getIndex():
            qualityElem.setIndex(new_index)
            self.data['downloaded_files'] = count
            bShouldRefresh = True
        
        #get the number of peers
        count = int(self.utility.getNumPeers())  
        print 'tb'
        print count                         
        #count = self.guiUtility.peer_manager.getCountOfSimilarPeers()
        aux_count = count
        if aux_count > 3000:
            aux_count = 3001
        if aux_count < 0:
            aux_count = 0
        new_index = int((aux_count-1)/750)+1 #from 0 to 5
        if new_index >= 4:
            new_index = 4
        overall_index = overall_index + new_index*0.1667
#        print "<mluc> [after similar peers] overall=",overall_index
        elem = self.getGuiElement("perf_Persons")    # Discovered persons
        if elem and new_index != elem.getIndex():
            elem.setIndex(new_index)
            self.data['similar_peers'] = count
            bShouldRefresh = True
        
        #get the number of files
        count = int(self.utility.getNumFiles())
        #count = self.data_manager.getRecommendFilesCount()
        aux_count = count
        if aux_count > 3000:
            aux_count = 3001
        if aux_count < 0:
            aux_count = 0
        new_index = int((aux_count-1)/750)+1 #from 0 to 5
        if new_index >= 4:
            new_index = 4
        overall_index = overall_index + new_index*0.1667
#        print "<mluc> [after taste files] overall=",overall_index
        elem = self.getGuiElement("perf_Files")    # Discovered files
        if elem and new_index != elem.getIndex():
            elem.setIndex(new_index)
            self.data['taste_files'] = count
            bShouldRefresh = True


        #set the download stuff
        dvalue = 0
        #get upload rate, download rate, upload slots: maxupload': '5', 'maxuploadrate': '0', 'maxdownloadrate': '0'
        maxuploadrate = self.guiUtility.utility.config.Read('maxuploadrate', 'int') #kB/s
        maxuploadslots = self.guiUtility.utility.config.Read('maxupload', "int")
        maxdownloadrate = self.guiUtility.utility.config.Read('maxdownloadrate', "int")
        value = 0
        if maxuploadrate == 0:
            value = 20
        else:
            value = maxuploadrate
            if maxuploadrate > 2000:
                value = 2000
            if maxuploadrate < 0:
                value = 0
            value = int(value/100)
        dvalue = dvalue + value
        value = 0
        if maxdownloadrate == 0:
            value = 20
        else:
            value = maxdownloadrate
            if maxdownloadrate > 2000:
                value = 2000
            if maxdownloadrate < 0:
                value = 0
            value = int(value/100)
        dvalue = dvalue + value
        value = 0
        if maxuploadslots == 0:
            value = 10
        else:
            value = maxuploadslots
            if maxuploadslots > 10:
                value = 10
            if maxuploadslots < 0:
                value = 0
            value = int(value)
        dvalue = dvalue + value
        #set the reachability value
        value = 0
        if self.guiUtility.isReachable:
            value = 20
        dvalue = dvalue + value
        #and the number of friends
        value = self.guiUtility.peer_manager.getCountOfFriends()
        self.data['friends_count'] = value
        if value > 20:
            value = 20
        if value < 0:
            value = 0
        dvalue = dvalue + value #from 0 to 90
        new_index  = int((dvalue-1)*0.0667+1) #from 0 to 6
        overall_index = overall_index + dvalue/60.0
#        print "<mluc> [after downloads] overall=",overall_index
        elem = self.getGuiElement("perf_Download")    # Optimal download speed
        if elem and new_index != elem.getIndex():
            elem.setIndex(new_index)
            bShouldRefresh = True

        
        #get the number of similar files (tasteful)
        count = self.guiUtility.peer_manager.getCountOfFriends()
        aux_count = count
        if aux_count > 100:
            aux_count = 101
        if aux_count < 0:
            aux_count = 0
        new_index = int((aux_count-1)/20)+1 #from 0 to 6
        overall_index = overall_index + new_index*0.1667
#        print "<mluc> [after taste files] overall=",overall_index
        elem = self.getGuiElement("perf_Presence")    # Network reach
        if elem and new_index != elem.getIndex():
            elem.setIndex(new_index)
            bShouldRefresh = True


#        print "<mluc> [before] overall index is",overall_index
        overall_index = int(overall_index)
        if overall_index > 6:
            overall_index = 6
#        print "<mluc> [after] overall index is",overall_index
        #set the overall performance to a random number
        new_index = overall_index #random.randint(0,5) #used only for testing
        elem = self.getGuiElement("perf_Overall")    # Overall performance
        if elem and new_index != elem.getIndex() or self.data.get('overall_rank') is None:
            elem.setIndex(new_index)
            if new_index < 2:
                self.data['overall_rank'] = "beginner"
                self.getGuiElement('text_Overall').SetLabel("Overall performance (beginner)")
            elif new_index < 4:
                self.data['overall_rank'] = "experienced"
                self.getGuiElement('text_Overall').SetLabel("Overall performance (experienced)")
            elif new_index < 6:
                self.data['overall_rank'] = "top user"
                self.getGuiElement('text_Overall').SetLabel("Overall performance (top user)")
            else:
                self.data['overall_rank'] = "master"
                self.getGuiElement('text_Overall').SetLabel("Overall performance (master)")
            bShouldRefresh = True
        
        if bShouldRefresh:
            self.Refresh()
            #also set data for details panel
            self.guiUtility.selectData(self.data)
        #wx.CallAfter(self.reloadData) #should be called from time to time
        if not self.timer:
            self.timer = wx.Timer(self, -1)
            self.Bind(wx.EVT_TIMER, self.reloadData, self.timer)
            self.timer.Start(5000)
        
    def OnMyInfoWizard(self, event = None):
        wizard = MyInfoWizard(self)
        wizard.RunWizard(wizard.getFirstPage())

    def WizardFinished(self,wizard):
        wizard.Destroy()

        self.getNameMugshot()
        self.showNameMugshot()
