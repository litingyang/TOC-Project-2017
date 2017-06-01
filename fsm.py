
import requests
from transitions.extensions import GraphMachine
import re

class TocMachine(GraphMachine):
    def __init__(self, **machine_configs):
        self.machine = GraphMachine(
            model = self,
            **machine_configs
        )

    def is_going_to_state1(self, update):
        text = update.message.text
        return text.lower() == 'help'

    def is_going_to_state2(self, update):
        text = update.message.text

        return (text.lower() == '查詢車次'or text.lower() == '2')

    def is_going_to_state3(self, update):
        text = update.message.text
        return (text.lower() == '列車時刻查詢'or text.lower() == '1')

    def is_going_to_state4(self, update):
        text = update.message.text
        pattern = "\s*\D*\s*(\d\d\d\d/\d\d/\d\d)\s*\D*(\d\d)[:|：]?(\d\d)\D*(\d\d)[:|：]?(\d\d)"
        match = re.search(pattern,text)
        if not match:
            update.message.reply_text("Bad request. Please enter again.")
            return 0
        day = match.group(1)
        ft = match.group(2) + match.group(3)
        tt = match.group(4) + match.group(5)

        twrail = 'http://twtraffic.tra.gov.tw/twrail'
        req = requests.get(twrail)
        regular =  "TRStation.push\('\d+'\);TRStation.push\('\d+'\);"+"TRStation.push\('([\u4E00-\u9FFF]+)'\)"
        stationlist = re.findall(regular,req.text)
        text = text.replace('台','臺')
        fs = ""
        ts = ""
        tmp = -1
        for i in range(0,len(stationlist),1):
            index = text.find(stationlist[i])
            if index > -1:
                if index > tmp:
                    tmp = index
                    fs = ts
                    ts = stationlist[i]
                else:
                    fs = stationlist[i]
        string = "起程站:"+ fs +"到達站:"+ ts +"日期:"+ day + "時間從" + ft + "至" + tt
        match = re.search(regular,req.text)
        self.message = string
        if fs!="" and ts!="":
            return 1
        else:
            update.message.reply_text("Bad request. Please enter again.")
            return 0

    def is_going_to_state5(self, update):
        text = update.message.text
        pattern = "\D*(\d\d\d\d/\d\d/\d\d)\D*(\d+)"
        match = re.search(pattern,text)
        self.message = text
        print("go to state5"+text)
        if match:
            return True
        else:
            update.message.reply_text("Bad request. Please enter again.")
            return False

    def on_enter_state1(self, update):
        string = "please enter: \n1.列車時刻查詢 \n2.查詢車次"
        update.message.reply_text(string)
        self.go_back(update)

    def on_exit_state1(self, update):
        print('Leaving state1')

    def on_enter_state2(self, update):
        update.message.reply_text("請輸入\n日期(ex:2017/06/08):\n車次(ex:129):")

    def on_exit_state2(self, update):
        print('Leaving state2')

    def on_enter_state3(self, update):
        update.message.reply_text("請輸入\n起程站(ex:臺北):\n到達站(ex:高雄):\n日期(ex:2017/06/08):\n時間從(ex:12:00)至(ex:23:59)")


    def on_exit_state3(self, update):
        print('Leaving state3')

    def on_enter_state4(self, update):
        input_text = self.message 
        print(input_text)
        pattern = "\s*起程站[:|：]\s*([\u4E00-\u9FFF]+)\s*到達站[:|：]\s*([\u4E00-\u9FFF]+)\s*日期[:|：]\s*(\d\d\d\d/\d\d/\d\d)\s*時間從(\d\d\d\d)至(\d\d\d\d)"
        twrail = 'http://twtraffic.tra.gov.tw/twrail'
        match = re.search(pattern,input_text)
        fs = match.group(1)
        ts = match.group(2)
        day = match.group(3)
        ft = match.group(4)
        tt = match.group(5)
        regular =  "TRStation.push\('(\d+)'\);TRStation.push\('(\d+)'\);"+"TRStation.push\('"+fs+"'\)"
        req = requests.get(twrail)
        match = re.search(regular,req.text)
        string = "查無此資料" 
        if match:
            fromcity = match.group(1)
            fromstation = match.group(2)
            regular =  "TRStation.push\('(\d+)'\);TRStation.push\('(\d+)'\);"+"TRStation.push\('"+ts+"'\)"
            match = re.search(regular,req.text)
            if match:
                tocity = match.group(1)
                tostation = match.group(2)
                payload = {'searchdate':day,'fromcity':fromcity,'tocity':tocity,'trainclass':'2','timetype':'1','fromstation':fromstation,'tostation':tostation,'fromtime':ft,'totime':tt}
                url = 'http://twtraffic.tra.gov.tw/twrail/SearchResult.aspx?searchtype=0'
                r = requests.get(url,params=payload)
                train = "<span id=\"classname\">([\u4E00-\u9FFF]+)</span>"
                number = "traincode=(\d+)"
                time = "<td class=\"SearchResult_Time\" align=\"center\" width=\"65\"><font color=\"Black\">(\d\d:\d\d)</font></td><td class=\"SearchResult_Time\" align=\"center\" width=\"65\"><font color=\"Black\">(\d\d:\d\d)</font></td><td align=\"center\" width=\"80\"><font color=\"Black\">(\d\d小時\d\d分)</font></td>"
                pay = "<span id=\"Label1\">(\$ \d+)</span>"
                trainlist = re.findall(train,r.text)
                numberlist = re.findall(number,r.text)
                timelist = re.findall(time,r.text)
                paylist = re.findall(pay,r.text)   
                if len(trainlist)>0:
                    string = ""
                    for i in range(0,min(len(trainlist),100),1):
                        string = string + "車種:" + trainlist[i] + " \n"
                        string = string + "車次:" + numberlist[i] + " \n"
                        string = string + fs + "開車時間:" + timelist[i][0] + " \n" + ts + "到達時間:" + timelist[i][1] + " \n" + "行駛時間:" + timelist[i][2]  + " \n"
                        string = string + "票價:" + paylist[i] + " "   
                        string = string + "\n\n" 


        update.message.reply_text(string)
        self.go_back(update)

    def on_exit_state4(self, update):
        print('Leaving state4')

    def on_enter_state5(self, update):
        input_text = self.message
        print(input_text)
        pattern = "\D*(\d\d\d\d/\d\d/\d\d)\D*(\d+)"
        match = re.search(pattern,input_text)
        string = "查無此資料" 
        if match:
            searchdate = match.group(1)
            traincode = match.group(2)
            url ="http://twtraffic.tra.gov.tw/twrail/mobile/TrainDetail.aspx?"
            payload = {'searchdate':searchdate,'traincode':traincode}
            r = requests.get(url,params=payload)
            train = "TRSearchResult.push\('([\u4E00-\u9FFF]+)'\);TRSearchResult.push\('(\d\d)(\d\d)'\);TRSearchResult.push\('(\d\d)(\d\d)'\);"
            trainlist = re.findall(train,r.text)
            if len(trainlist)>0:
                string = ""
                for i in range(0,min(len(trainlist),100),1):
                    string = string + "站名:" + trainlist[i][0] + " \n"
                    string = string + "到達時間:" + trainlist[i][1] + ":" + trainlist[i][2] + " \n"
                    string = string + "開車時間:" + trainlist[i][3] + ":" + trainlist[i][4] + " "
                    string = string + "\n\n"  

        update.message.reply_text(string)
        self.go_back(update)

    def on_exit_state5(self, update):
        print('Leaving state5')
