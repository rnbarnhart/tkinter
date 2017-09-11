#!/usr/bin/python3
import Tkinter as tk
import ttk
import tkFont
from Tkinter import *
import tkMessageBox
import tkFileDialog
from tkFileDialog import askdirectory, askopenfilename
import getpass, zipfile, os, csv, datetime, subprocess #################################### need to remove os function at some point
from ScrolledText import *
from util.configuration import Configuration
from util.connection import Connection
from psycopg2.extensions import AsIs, ISOLATION_LEVEL_AUTOCOMMIT
from util.logger import Logger
import logging
import psycopg2
import urllib2
from CIF_Mod import CIF
from GRIP import initialize, run_checks, export2shp
import time, stat
from dbCleanup import dbCleanup

'''
Program notes:
- 07/19/2017
  . Removed references to Python 3
  . Added use of configuration library to retrieve information from access.ini file
  . Added database connection to extract data from cif.cif_result table. 
  .       note: Current sql statement just retrieves 15 records. 
  .             Will need to refine to select data based on current user
  . Added sort capabilities, by clicking on column title, but need to display a note for the user
  .
- 08/02/2017
  - Added log viewer and error screen
  - Added import instruction for time and stat
  - Added dbCleanup 
'''

class CIFUI( tk.Frame ):
    def __init__(self, *args, **kwargs):
        tk.Frame.__init__(self, *args, **kwargs)
        self.config = Configuration()        
        # log_opts = self.config.mapSection('Log')        
        # self.log = (Logger(log_opts['Log'],'/log')).getLoggerInstance()
        self.log = logging.basicConfig(filename= 'cif.log',level=logging.DEBUG) 
        #screen dimensions
        height=600
        width=800
        #center screen
        screen_width = self.master.winfo_screenwidth()
        screen_height = self.master.winfo_screenheight()
        x = (screen_width/2) - (width/2)
        y = (screen_height/2) - (height/2)
        self.master.geometry('%dx%d+%d+%d'%(width, height, x, y))        
        #screen title
        self.master.title( "Run CIF Checks" )
        self.form1()
        self.menu()

    def menu(self):
        self.master.attributes('-topmost', False)
        self.master.option_add('*tearOff','FALSE')
        self.menubar = tk.Menu(self.master)
        self.menu_file = tk.Menu(self.menubar)
        self.menu_help = tk.Menu(self.menubar)
        
        self.menu_file.add_command(label='Exit', command=self.on_quit)
        self.menubar.add_cascade(menu=self.menu_file, label='File')

        self.menubar.add_cascade(menu=self.menu_help, label='Help')
        self.menu_help.add_command(label='About', command=self.on_about)

        self.master.config(men=self.menubar)
        
    def on_quit(self):
        self.master.destroy()

    def startCleanup(self):
        self.dbc = dbCleanup(self.zz)
        #print self.zz
        self.progress["value"] = 0
        self.maxbytes = 50000
        self.progress["maximum"] = 50000
        self.read_bytes()
        
    def read_bytes(self):
        self.bytes += 500
        self.progress["value"] = self.bytes
        if self.bytes < self.maxbytes:
            self.x = self.x + 1
            if self.x > 9:
                if self.anbr == 1:
                    self.dbc.chkarchive(self.zz)
                elif self.anbr == 2:
                    self.dbc.chklog(self.zz)
                self.anbr = self.anbr + 1

                self.x = 0
            self.after(100, self.read_bytes)
        
    def grab_and_assign(self, event):
        self.zz = self.var.get()
    
    def on_dbcleanup(self):
        win = tk.Tk()
        height=300
        width=600
        screen_width = win.winfo_screenwidth()
        screen_height = win.winfo_screenheight()
        x = (screen_width/2) - (width/2)
        y = (screen_height/2) - (height/2)
        win.geometry('%dx%d+%d+%d'%(width, height, x, y))
        win.wm_title('dbCleanup Routine')
        self.anbr = 0 
        self.bytes = 0
        self.maxbytes = 0
        self.x = 0
        self.var = tk.StringVar(win)
        self.zz = '40'
        choices = ['40','35','30', '25','20']
        self.var.set(choices[0])
        option = OptionMenu(win, self.var, *choices, command=self.grab_and_assign)

        option.place(x=200,y=80)
        Label(win, text='Delete files older than ').place(x=50, y=80)
        self.button = ttk.Button(win, text="Start", command=self.startCleanup)
        self.button.place(x=300,y=170, anchor='center')
        self.progress = ttk.Progressbar(win, orient="horizontal", length=500, mode="determinate")
        self.progress.place(x=50, y=120)
        winb1 = tk.Button(win, text='Close', command=win.destroy)
        winb1.place(x=300,y=280, anchor='center')  

    def on_about(self):
        win = tk.Tk()
        height=100
        width=200
        screen_width = win.winfo_screenwidth()
        screen_height = win.winfo_screenheight()
        x = (screen_width/2) - (width/2)
        y = (screen_height/2) - (height/2)
        win.geometry('%dx%d+%d+%d'%(width, height, x, y))
        win.wm_title('About')
        winlm = tk.Label(win, text='uProcess 1.0', anchor='center', font='bold')
        winlm.place(x=100, y=30, anchor='center')
        winb1 = tk.Button(win, text='ok', command=win.destroy)
        winb1.place(x=100,y=60, anchor='center')

    def on_config(self):
        win = tk.Tk()
        height=200
        width=600
        screen_width = win.winfo_screenwidth()
        screen_height = win.winfo_screenheight()
        x = (screen_width/2) - (width/2)
        y = (screen_height/2) - (height/2)
        win.geometry('%dx%d+%d+%d'%(width, height, x, y))
        
        psqlStr = "SELECT config.name, config.location FROM cif.config;"
        self.dbconnect()
        curs = self.getCursor()
        curs.execute(psqlStr)
        data = curs.fetchall()        
        
        win.wm_title('Config')
        xpos = 0

        winlm0 = tk.Label(win, text='These are the preset location of folders for files used by the program.').place(x=30, y=20+xpos)
                    
        for row in data:
            winlm1 = tk.Label(win, text='NAME: ').place(x=30, y=50+xpos)
            winlm2 = tk.Label(win, text=row[0]).place(x=80, y=50+xpos)
            winlm3 = tk.Label(win, text='LOCATION: ').place(x=140, y=50+xpos)
            winlm4 = tk.Label(win, text=row[1]).place(x=220, y=50+xpos)
            xpos = xpos + 20
        #winlm2 = tk.Label(win, text=data[1], anchor='center', font='bold')
        #winlm2.place(x=100, y=50, anchor='center')

        winb1 = tk.Button(win, text='Close Window', command=win.destroy)
        winb1.place(x=300,y=160, anchor='center')

    def dbconnect(self):
        db_opts = self.config.mapSection("Database")
        self.name = db_opts['name']
        self.user = db_opts['user']
        self.password = db_opts['passwd']
        self.host = db_opts['host']
        self.cursor = None
        self.connection = psycopg2.connect('dbname={} user={} password={} '\
            ' host={}'.format(self.name, self.user, self.password, self.host))
        self.connection.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        return True
        
    def getCursor(self, name=None):
        if name:
            self.cursor = self.connection.cursor(name)
        else:
            self.cursor = self.connection.cursor()
        return self.cursor

    def close(self):
        self.cursor.close()
        self.connection.close()
        return True

    def no_Logfile(self):
        win = tk.Tk()
        height=110
        width=300
        screen_width = win.winfo_screenwidth()
        screen_height = win.winfo_screenheight()
        x = (screen_width/2) - (width/2)
        y = (screen_height/2) - (height/2)
        win.geometry('%dx%d+%d+%d'%(width, height, x, y))
        win.wm_title('No Log File')
        data = str(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()) + '\n\n') + str('No_log_file_available')        
        winlm = tk.Label(win, text=data, anchor='center')
        winlm.place(x=150, y=40, anchor='center')
        winb1 = tk.Button(win, text='Close Window', command=win.destroy)
        winb1.place(x=150,y=90, anchor='center')

    def displayLog(self):
        try:
            f = open('log', 'r')
            data = f.readlines()

            win1 = tk.Tk()
            height = 300
            width = 1300
            screen_width = win1.winfo_screenwidth()
            screen_height = win1.winfo_screenheight()
            x = (screen_width/2) - (width/2)
            y = (screen_height/2) - (height/2)
            win1.geometry('%dx%d+%d+%d'%(width, height, x, y))
            win1.wm_title('View Log')        
            display_header = ['Date'.ljust(10), 'Time'.ljust(10), 'Area'.ljust(15), 'Module'.ljust(15),'Function'.ljust(15), 'Info'.ljust(60)]        
            s = """\click on header to sort by that column to change width of column drag boundary"""        
            msg = ttk.Label(win1, wraplength="4i", justify="center", anchor="n", padding=(10, 2, 10, 6))
            container = ttk.Frame(win1, width=width, height=height)
            container.grid(row=0, column=0,sticky=(W, E), padx=10, pady=10)
            self.tree = ttk.Treeview(win1, column=display_header, show='headings')
            vsb = ttk.Scrollbar(win1, orient="vertical", command=self.tree.yview)
            hsb = ttk.Scrollbar(win1, orient="horizontal", command=self.tree.xview) 
            self.tree.configure(yscrollcommand=vsb.set,xscrollcommand=hsb.set)
            self.tree.grid(row=1, column=1,  in_=container, ipadx=100, sticky='W, E', columnspan=4)
            container.columnconfigure(0, weight=1)
            container.rowconfigure(0, weight=1)
        
            for col in display_header:
                self.tree.heading(col, text=col.title(),
                    command=lambda c=col: self.sortby(self.tree, c, 0))
                # adjust the column's width to the header string
                self.tree.column(col,
                    width=tkFont.Font().measure(col.title()))

            for item in data:
                self.tree.insert('', 'end', values=item)
                for ix, val in enumerate(item):
                    col_w = tkFont.Font().measure(val)  
                    #       if self.tree.column(display_header[ix],width=None)<col_w:
                    #           self.tree.column(display_header[ix], width=col_w)        

            winb1 = tk.Button(win1, text='Close', command=win1.destroy)
            winb1.place(x=650,y=280, anchor='center') 

        except:
            self.no_Logfile()

    # def setup_histdisplay(self):
    #     hist_header = ['Comp_Time', 'GDB Name', 'WMS_URL']
    #     s = """\click on header to sort by that column to change width of column drag boundary"""
    #     msg = ttk.Label(wraplength="4i", justify="left", anchor="n", padding=(10, 2, 10, 6), text=s)
    #     msg.pack(fill='x')
    #     container = ttk.Frame()
    #     container.pack(fill='both', expand=True)
    #     # create a treeview with dual scrollbars
    #     self.tree = ttk.Treeview(columns=hist_header, show="headings")
    #     vsb = ttk.Scrollbar(orient="vertical", command=self.tree.yview)
    #     hsb = ttk.Scrollbar(orient="horizontal", command=self.tree.xview)
    #     self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
    #     self.tree.grid(column=0, row=0, sticky='nsew', in_=container)
    #     vsb.grid(column=1, row=0, sticky='ns', in_=container)
    #     hsb.grid(column=0, row=1, sticky='ew', in_=container)
    #     container.grid_columnconfigure(0, weight=1)
    #     container.grid_rowconfigure(0, weight=1)
        
    def run_history(self):
        win = tk.Tk()
        height=300
        width=1300

        screen_width = win.winfo_screenwidth()
        screen_height = win.winfo_screenheight()
        x = (screen_width/2) - (width/2)
        y = (screen_height/2) - (height/2)
        win.geometry('%dx%d+%d+%d'%(width, height, x, y))
        win.wm_title('Run History')        
        
        hist_header = ['Comp_Time', 'GDB Name', 'WMS_URL']        
        s = """\click on header to sort by that column to change width of column drag boundary"""        
        msg = ttk.Label(win, wraplength="4i", justify="center", anchor="n", padding=(10, 2, 10, 6))
        container = ttk.Frame(win, width=width, height=height)
        container.grid(row=0, column=0,sticky=(W, E), padx=10, pady=10)
        self.tree = ttk.Treeview(win, column=hist_header, show='headings')
        vsb = ttk.Scrollbar(win, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(win, orient="horizontal", command=self.tree.xview) 
        self.tree.configure(yscrollcommand=vsb.set,xscrollcommand=hsb.set)
        self.tree.grid(row=1, column=1,  in_=container, ipadx=100, sticky='W, E', columnspan=4)
        container.columnconfigure(0, weight=1)
        container.rowconfigure(0, weight=1)
          
        psqlStr = "SELECT distinct cif_results.comp_time, cif_results.gdb_name, cif_results.results_wms_url FROM cif.cif_results limit 15;"
        self.dbconnect()
        curs = self.getCursor()
        curs.execute(psqlStr)
        data = curs.fetchall()
        
        for col in hist_header:
            self.tree.heading(col, text=col.title(),
                command=lambda c=col: self.sortby(self.tree, c, 0))
            # adjust the column's width to the header string
            self.tree.column(col,
                width=tkFont.Font().measure(col.title()))
        
        for item in data:
            # hyperlink = urllib2.urlopen(item[2])
            # self.tree.insert('', 'end', values=item[0|1])
            # self.tree.insert('', 'end', values= hyperlink.read())
            
            self.tree.insert('', 'end', values=item)
            
            #self.tree.insert('', 'end', values="item %'{}'".format(item))
            #self.tree.insert('', 'end', values="item %s"%item)
            
            # adjust column's width if necessary to fit each value
            for ix, val in enumerate(item):
                col_w = tkFont.Font().measure(val)  
                if self.tree.column(hist_header[ix],width=None)<col_w:
                    self.tree.column(hist_header[ix], width=col_w)

        self.tree.bind("<Double-1>", self.OnDoubleClick)
        winb1 = tk.Button(win, text='Close', command=win.destroy)
        winb1.place(x=650,y=280, anchor='center')

    def OnDoubleClick(self, event):
        itemx = self.tree.selection()[0]
        print("You clicked on", self.tree.item(itemx,"values"))

    def sortby(self, tree, col, descending):
        data = [(tree.set(child, col), child) for child in tree.get_children('')]
        data.sort(reverse=descending)
        for ix, item in enumerate(data):
            tree.move(item[1], '', ix)
        tree.heading(col, command=lambda col=col: self.sortby(tree, col, int(not descending)))

    def run_config(self):
        win = tk.Tk()
        height=200
        width=500
        screen_width = win.winfo_screenwidth()
        screen_height = win.winfo_screenheight()
        x = (screen_width/2) - (width/2)
        y = (screen_height/2) - (height/2)
        win.geometry('%dx%d+%d+%d'%(width, height, x, y))
        win.wm_title('History Log')
        winlm = tk.Label(win, text='User ID', width=10)
        winlm.grid(row=1, column=0, sticky='w')
        winsv = StringVar(win, value='John Doe')
        winle = tk.Entry(win, width=40, textvariable=winsv)
        winle.grid(row=1, column=1, sticky='e') 
        winb1 = tk.Button(win, text='ok', command=win.destroy)
        winb1.place(x=width/2,y=100, anchor='center')

    def form1(self):
        # Left Side of Screen
        
        ls0 = tk.LabelFrame(self.master, text="Project Info", padx=5, pady=5, width=50)
        ls0.grid(row=2, column=0, columnspan=5, sticky='e', padx=5, pady=0, ipadx=0, ipady=0)
       
        l0 = tk.Label(ls0, text="Project ID", width=10)
        l0.grid(row=1, column=0, sticky='w')
        l1v = tk.StringVar(ls0, value='12345')  
        l1 = tk.Entry(ls0, width=30, textvariable=l1v)
        l1.grid(row=1, column=1, sticky='w')
        l2 = tk.Label(ls0, text="User Name", width=10)
        l2.grid(row=2, column=0, sticky='w')
        l1vv = tk.StringVar(ls0, value=str(getpass.getuser()))  
        l3 = tk.Entry(ls0, width=30, textvariable=l1vv)
        l3.configure(state = 'disabled')
        l3.grid(row=2, column=1, sticky='w')


        # Right Side of Screen

        right0 = tk.LabelFrame(self.master, text="Run Info", padx=5, pady=5, width=50, height=10)
        right0.grid(row=2, column=6, columnspan=10, sticky='w', padx=5, pady=5, ipadx=0, ipady=0)
        b1 = tk.Button(right0, text="JSON Selection", command=self.run_history)
        b1.grid(row=1, column=0, sticky='w', padx=5, pady=5, ipadx=5, ipady=0)
        b2 = tk.Button(right0, text="View Log", command=self.run_config)
        b2.grid(row=1, column=6, sticky='e', padx=5, pady=5, ipadx=5, ipady=0)
        
        
        # Center of screen
        
        def btnbrowse():
        #   filelocation = tkFileDialog.askdirectory(initialdir = "/Home:", title = "Select GDB")
            filelocation = tkFileDialog.askopenfilename(initialdir = "/Home:", title = "Select GDB Zip")
            gdb_link.set(filelocation)
            textarray.insert(END, filelocation)

        # Label and browse set up to input GDB
        lbl = tk.LabelFrame(self.master, text = "Parameters", padx=5, pady=5, width=108)
        lbl.grid(row = 3, column = 0, columnspan=10, sticky='w', padx=5, pady=10, ipadx=0, ipady=0)
        lbl.gdb= tk.Label(lbl, text = "Select GDB to Load", padx=5, pady=5)
        lbl.gdb.grid(row = 1, column = 0, columnspan=2)
        gdb_link = tk.StringVar()
        gdb = tk.Entry(lbl, textvariable = gdb_link, width = 86)
        gdb.grid(row = 2, column = 0)
        button_browse = tk.Button(lbl, text = " Browse ", command = btnbrowse)
        button_browse.grid(row = 2, column = 1)


        # Label for dropdown schema selection
        lbl.schema = tk.LabelFrame(lbl, text = "Select Schema", labelanchor='n', padx=5, pady=5)
        lbl.schema.grid(row = 3, column = 0, columnspan=2, padx=5, pady=10, ipadx=0, ipady=0)
        tkvar = StringVar()

        # Dictionary with options for dropdown schema selection
        choices = {'   ','TDS','TFDM','MGCP','AFD','SAC'}
        tkvar.set('   ') # set the default option
        popupMenu = OptionMenu(lbl.schema, tkvar, *choices)
        popupMenu.grid(row = 1, column = 0, columnspan=2, padx=10, pady=5)

        
        def btnrun():
            process_scripts = {'CIF01':[CIF01Var,'allotherillegalfaces'], 'CIF02':[CIF02Var,'bldginbuacheck'], 'CIF03':[CIF03Var,'daminhydrocheck'], 'CIF04':[CIF04Var,'islandcheck'], 'CIF05':[CIF05Var,'tidalwaterinswampcheck'],
                               'CIF06':[CIF06Var,'internal_kink'], 'CIF07':[CIF07Var,'line_feature_join_kink'], 'CIF08':[CIF08Var,'line_kickback'], 'CIF09':[CIF09Var,'line_kink'], 'CIF10':[CIF10Var,'latmismatchcheck11'],
                               'CIF11':[CIF11Var,'longmismatchcheck11'], 'CIF12':[CIF12Var,'latmergecheck'], 'CIF13':[CIF13Var,'longmergecheck'], 'CIF14':[CIF14Var,'getselfintersections'], 'CIF15':[CIF15Var,'multipartcrv'], 
                               'CIF16':[CIF16Var,'multipartpnt'], 'CIF17':[CIF17Var,'multipartsrf'], 'CIF18':[CIF18Var,'checkinvalidrings'], 'CIF19':[CIF19Var,'nullsubattributecheck'], 'CIF20':[CIF20Var,'getlineovershoots'], 
                               'CIF21':[CIF21Var,'getlineundershoots'], 'CIF22':[CIF22Var,'featurelvlmetachk'], 'CIF23':[CIF23Var,'featurelvlmetachkmetadatasrf'], 'CIF24':[CIF24Var,'featurelvlmetachkresourcesrf'], 'CIF25':[CIF25Var,'mstrwidthfndr'], 
                               'CIF26':[CIF26Var,'getduplicatefeatures'], 'CIF27':[CIF27Var,'mstrsclfndr'], 'CIF28':[CIF28Var,'vsncheck'], 'CIF29':[CIF29Var,'bfccheck'], 'CIF30':[CIF30Var,'latonedegcheck'],
                               'CIF31':[CIF31Var,'longonedegcheck'], 'CIF32':[CIF32Var,'lmccheck'], 'CIF33':[CIF33Var,'grndtranintersectbldg3'], 'CIF34':[CIF34Var,'getshortlengthfeatures'], 'CIF35':[CIF35Var,'illogAttributes'],
                               'CIF36':[CIF36Var,'linetolineintersections'], 'CIF37':[CIF37Var,'isftrdirchange'], 'CIF38':[CIF38Var,'bldginperrwtrs'], 'CIF39':[CIF39Var,'grndtraninperwtrs'], 'CIF40':[CIF40Var,'latmismatchcheck6'],
                               'CIF41':[CIF41Var,'longmismatchcheck6'], 'CIF42':[CIF42Var,'sliverfind'], 'CIF43':[CIF43Var,'grndtranintersectbldg8'], 'CIF44':[CIF44Var,'startendcheck']}

            run_script = tkMessageBox.askyesno('Run Checks?', 'Would you like to run checks on\n' + os.path.basename(gdb_link.get()[0:-4])) 
            if run_script == True:
                checks_lst = []
                textarray.insert(END, '\nInput GDB: ' + os.path.basename(gdb_link.get()[0:-4]), 'name')

                # Loop through selected checkboxes and append associated check to list
                for checked in process_scripts:
                    testing = process_scripts.get(checked)[0]
                    if testing.get() == 1:
                        startfile = process_scripts.get(checked)[1]
                        checks_lst.append(startfile)
                # schema = tkvar.get()
                # for chks in checks.get(schema):
                #     # textarray.insert(END, '\nRunning ' + str(process_scripts.get(chks)[0]) + ' checks', 'cifs')
                #     startfile = process_scripts.get(chks)[1]
                #     checks_lst.append(startfile)
                
                print checks_lst
                reformat_lst = ", ".join( repr(e) for e in checks_lst)
                str_lst = str(reformat_lst.replace("'", ""))

                time = datetime.datetime.now()
                submit_time = time.strftime("%Y%m%d_%H%M_%f")
                precheck_time = time.strftime("%Y-%m-%d %H:%M:%S.%f-05")
                # submit_time = timezone.now().strftime("%Y%m%d_%H%M_%f")
                GIS_DB = "gdb_" + submit_time + "_"
                print GIS_DB
                textarray.insert(END, "\nPostgres GDB Name: " + GIS_DB, 'name')
                

                data = gdb_link.get()
                textfile = os.path.join(os.path.dirname(data), 'job_info.txt')
                file = open(textfile, 'w')
                file.write(l1v.get() + '\t' + data[:-4] + '\t' + GIS_DB + '\t' + precheck_time + '\t' + '1' + '\t' + str_lst)
                file.close()

                # Works perfectly....
                # os.system('pgsql2shp -f /home/barnharn/uprocess/media/temp/exported_shapes -h localhost -u postgres -P postgres gdb_20170811_1512_724940_ "SELECT * FROM public.hydrographycrv"')
                
                textarray.insert(END, '\nUnzipped and running Pre-Checks')
                initialize(data)
                textarray.insert(END, '\nRunning selected CIF Checks')
                run_checks(l1v.get(), GIS_DB, 1, str_lst, checks_lst)
                textarray.insert(END, '\nCreating shapefiles containing feature errors')
                export2shp(GIS_DB)

                textarray.insert(END, '\n\n----Completed processing----')
                textarray.insert(END, '\n\n----Select JSON Selection button to download results---')
            #     print 'Cancelled'


        def btnclose():
            self.master.destroy()

        def change_dropdown(*args):
            chks = checks.get('   ')
            for chk in chks:
                chk.deselect()
            dropvar = tkvar.get()
            if dropvar != '   ':
        #    for index, values in enumerate()
                chks = checks.get(dropvar)
                for chk in chks:
                    chk.select()


        # Label and new data window frame for checkboxes
        lbl.cifchecks = tk.LabelFrame(lbl, text="Select CIF Checks", labelanchor='n', padx=5, pady=5, width=50)
        lbl.cifchecks.grid(row=5, column=0, columnspan=8, padx=5, pady=5, ipadx=0, ipady=0)
        ## Set variable checkboxes
        CIF01Var = IntVar()
        CIF01 = Checkbutton(lbl.cifchecks, variable = CIF01Var, text = " CIF01")
        CIF01.grid(row = 3, column = 0)
        CIF02Var = IntVar()
        CIF02 = Checkbutton(lbl.cifchecks, variable = CIF02Var, text = " CIF02")
        CIF02.grid(row = 3, column = 1)
        CIF03Var = IntVar()
        CIF03 = Checkbutton(lbl.cifchecks, variable = CIF03Var, text = " CIF03")
        CIF03.grid(row = 3, column = 2)
        CIF04Var = IntVar()
        CIF04 = Checkbutton(lbl.cifchecks, variable = CIF04Var, text = " CIF04")
        CIF04.grid(row = 3, column = 3)
        CIF05Var = IntVar()
        CIF05 = Checkbutton(lbl.cifchecks, variable = CIF05Var, text = " CIF05")
        CIF05.grid(row = 3, column = 4)
        CIF06Var = IntVar()
        CIF06 = Checkbutton(lbl.cifchecks, variable = CIF06Var, text = " CIF06")
        CIF06.grid(row = 3, column = 5)
        CIF07Var = IntVar()
        CIF07 = Checkbutton(lbl.cifchecks, variable = CIF07Var, text = " CIF07")
        CIF07.grid(row = 3, column = 6)
        CIF08Var = IntVar()
        CIF08 = Checkbutton(lbl.cifchecks, variable = CIF08Var, text = " CIF08")
        CIF08.grid(row = 3, column = 7)
        CIF09Var = IntVar()
        CIF09 = Checkbutton(lbl.cifchecks, variable = CIF09Var, text = " CIF09")
        CIF09.grid(row = 3, column = 8)
        CIF10Var = IntVar()
        CIF10 = Checkbutton(lbl.cifchecks, variable = CIF10Var, text = " CIF10")
        CIF10.grid(row = 3, column = 9)
        CIF11Var = IntVar()
        CIF11 = Checkbutton(lbl.cifchecks, variable = CIF11Var, text = " CIF11")
        CIF11.grid(row = 4, column = 0)
        CIF12Var = IntVar()
        CIF12 = Checkbutton(lbl.cifchecks, variable = CIF12Var, text = " CIF12")
        CIF12.grid(row = 4, column = 1)
        CIF13Var = IntVar()
        CIF13 = Checkbutton(lbl.cifchecks, variable = CIF13Var, text = " CIF13")
        CIF13.grid(row = 4, column = 2)
        CIF14Var = IntVar()
        CIF14 = Checkbutton(lbl.cifchecks, variable = CIF14Var, text = " CIF14")
        CIF14.grid(row = 4, column = 3)
        CIF15Var = IntVar()
        CIF15 = Checkbutton(lbl.cifchecks, variable = CIF15Var, text = " CIF15")
        CIF15.grid(row = 4, column = 4)
        CIF16Var = IntVar()
        CIF16 = Checkbutton(lbl.cifchecks, variable = CIF16Var, text = " CIF16")
        CIF16.grid(row = 4, column = 5)
        CIF17Var = IntVar()
        CIF17 = Checkbutton(lbl.cifchecks, variable = CIF17Var, text = " CIF17")
        CIF17.grid(row = 4, column = 6)
        CIF18Var = IntVar()
        CIF18 = Checkbutton(lbl.cifchecks, variable = CIF18Var, text = " CIF18")
        CIF18.grid(row = 4, column = 7)
        CIF19Var = IntVar()
        CIF19 = Checkbutton(lbl.cifchecks, variable = CIF19Var, text = " CIF19")
        CIF19.grid(row = 4, column = 8)
        CIF20Var = IntVar()
        CIF20 = Checkbutton(lbl.cifchecks, variable = CIF20Var, text = " CIF20")
        CIF20.grid(row = 4, column = 9)
        CIF21Var = IntVar()
        CIF21 = Checkbutton(lbl.cifchecks, variable = CIF21Var, text = " CIF21")
        CIF21.grid(row = 5, column = 0)
        CIF22Var = IntVar()
        CIF22 = Checkbutton(lbl.cifchecks, variable = CIF22Var, text = " CIF22")
        CIF22.grid(row = 5, column = 1)
        CIF23Var = IntVar()
        CIF23 = Checkbutton(lbl.cifchecks, variable = CIF23Var, text = " CIF23")
        CIF23.grid(row = 5, column = 2)
        CIF24Var = IntVar()
        CIF24 = Checkbutton(lbl.cifchecks, variable = CIF24Var, text = " CIF24")
        CIF24.grid(row = 5, column = 3)
        CIF25Var = IntVar()
        CIF25 = Checkbutton(lbl.cifchecks, variable = CIF25Var, text = " CIF25")
        CIF25.grid(row = 5, column = 4)
        CIF26Var = IntVar()
        CIF26 = Checkbutton(lbl.cifchecks, variable = CIF26Var, text = " CIF26")
        CIF26.grid(row = 5, column = 5)
        CIF27Var = IntVar()
        CIF27 = Checkbutton(lbl.cifchecks, variable = CIF27Var, text = " CIF27")
        CIF27.grid(row = 5, column = 6)
        CIF28Var = IntVar()
        CIF28 = Checkbutton(lbl.cifchecks, variable = CIF28Var, text = " CIF28")
        CIF28.grid(row = 5, column = 7)
        CIF29Var = IntVar()
        CIF29 = Checkbutton(lbl.cifchecks, variable = CIF29Var, text = " CIF29")
        CIF29.grid(row = 5, column = 8)
        CIF30Var = IntVar()
        CIF30 = Checkbutton(lbl.cifchecks, variable = CIF30Var, text = " CIF30")
        CIF30.grid(row = 5, column = 9)
        CIF31Var = IntVar()
        CIF31 = Checkbutton(lbl.cifchecks, variable = CIF31Var, text = " CIF31")
        CIF31.grid(row = 6, column = 0)
        CIF32Var = IntVar()
        CIF32 = Checkbutton(lbl.cifchecks, variable = CIF32Var, text = " CIF32")
        CIF32.grid(row = 6, column = 1)
        CIF33Var = IntVar()
        CIF33 = Checkbutton(lbl.cifchecks, variable = CIF33Var, text = " CIF33")
        CIF33.grid(row = 6, column = 2)
        CIF34Var = IntVar()
        CIF34 = Checkbutton(lbl.cifchecks, variable = CIF34Var, text = " CIF34")
        CIF34.grid(row = 6, column = 3)
        CIF35Var = IntVar()
        CIF35 = Checkbutton(lbl.cifchecks, variable = CIF35Var, text = " CIF35")
        CIF35.grid(row = 6, column = 4)
        CIF36Var = IntVar()
        CIF36 = Checkbutton(lbl.cifchecks, variable = CIF36Var, text = " CIF36")
        CIF36.grid(row = 6, column = 5)
        CIF37Var = IntVar()
        CIF37 = Checkbutton(lbl.cifchecks, variable = CIF37Var, text = " CIF37")
        CIF37.grid(row = 6, column = 6)
        CIF38Var = IntVar()
        CIF38 = Checkbutton(lbl.cifchecks, variable = CIF38Var, text = " CIF38")
        CIF38.grid(row = 6, column = 7)
        CIF39Var = IntVar()
        CIF39 = Checkbutton(lbl.cifchecks, variable = CIF39Var, text = " CIF39")
        CIF39.grid(row = 6, column = 8)
        CIF40Var = IntVar()
        CIF40 = Checkbutton(lbl.cifchecks, variable = CIF40Var, text = " CIF40")
        CIF40.grid(row = 6, column = 9)
        CIF41Var = IntVar()
        CIF41 = Checkbutton(lbl.cifchecks, variable = CIF41Var, text = " CIF41")
        CIF41.grid(row = 7, column = 0)
        CIF42Var = IntVar()
        CIF42 = Checkbutton(lbl.cifchecks, variable = CIF42Var, text = " CIF42")
        CIF42.grid(row = 7, column = 1)
        CIF43Var = IntVar()
        CIF43 = Checkbutton(lbl.cifchecks, variable = CIF43Var, text = " CIF43")
        CIF43.grid(row = 7, column = 2)
        CIF44Var = IntVar()
        CIF44 = Checkbutton(lbl.cifchecks, variable = CIF44Var, text = " CIF44")
        CIF44.grid(row = 7, column = 3)


        ## On change of dropdown value
        checks = {'   ':[CIF01, CIF02, CIF03, CIF04, CIF05, CIF06, CIF07, CIF08, CIF09, CIF10,
                         CIF11, CIF12, CIF13, CIF14, CIF15, CIF16, CIF17, CIF18, CIF19, CIF20, 
                         CIF21, CIF22, CIF23, CIF24, CIF25, CIF26, CIF27, CIF28, CIF29, CIF30,
                         CIF31, CIF32, CIF33, CIF34, CIF35, CIF36, CIF37, CIF38, CIF39, CIF40,
                         CIF41, CIF42, CIF43, CIF44],
                  'TDS':[CIF01, CIF02, CIF03, CIF04, CIF05, CIF06, CIF07, CIF08, CIF09, CIF10,
                         CIF11, CIF12, CIF13, CIF14, CIF15, CIF16, CIF17, CIF18, CIF19, CIF20, 
                         CIF21, CIF22, CIF23, CIF24, CIF25, CIF26, CIF27, CIF28, CIF29, CIF30],
                  'TFDM':[CIF02, CIF03, CIF04, CIF05, CIF07, CIF08, CIF09, CIF10,
                         CIF12, CIF13, CIF14, CIF15, CIF17, CIF18, CIF19, CIF20, 
                         CIF22, CIF23, CIF24, CIF25, CIF27, CIF28, CIF29, CIF30],
                  'MGCP':[CIF11, CIF12, CIF13, CIF14, CIF15, CIF16, CIF17, CIF18, CIF19, CIF20],
                  'AFD':[CIF21, CIF22, CIF23, CIF24, CIF25, CIF26, CIF27, CIF28, CIF29, CIF30],
                  'SAC':[CIF10, CIF20, CIF30]}


         ## Link function to change dropdown
        tkvar.trace('w', change_dropdown)


        ## User group predetermined checks
        user_dict = {'barnharn':'AFD', 'terrytb':'MGCP', 'chapmaca':'TFDM', 'tacketmt':'TDS'}
        user_nam = str(getpass.getuser())
        if user_nam in user_dict:
            user_pref = user_dict.get(user_nam)
            tkvar.set(user_pref)
            for chks in checks.get(user_pref):
                chks.select()
        else:
            print "User does not belong to a group"


        button_run = tk.Button(lbl, text = " Run CIF checks ", command = btnrun)
        button_run.grid(row = 10, column = 0, columnspan=2, pady = 5)

        button_close = tk.Button(lbl, text = " Close Window ", command = btnclose)
        button_close.grid(row = 11, column = 0, columnspan=2, pady = 5)

        lbl.textarray = tk.LabelFrame(self.master, text="Processing Info", padx=5, pady=5, width=108, height=10)
        lbl.textarray.grid(row=8, column=0, columnspan=10, sticky='e', padx=5, pady=0, ipadx=0, ipady=0)
        textarray = ScrolledText(lbl.textarray, width = 108, height = 7)
        textarray.grid(row = 0, column = 0, pady = 5)
        
def main():
    root = tk.Tk()
    view = CIFUI(root)
    #view.pack(side="top", fill="both")
    root.mainloop()   

if __name__ == "__main__":
   main()


