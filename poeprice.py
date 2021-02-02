import tkinter as tk
from tkinter import ttk
import webbrowser
import requests
import codecs
from tempfile import NamedTemporaryFile
import threading
import time
import json
import os.path

config = {'useragent':'Mozilla/5.0', 'ssid':'SSID', 'account':'Account Name', 'ref':'Reference League Name', 'priv':'Private League Name','preset':[]}
if os.path.isfile('config.json'):
    with open('config.json','r') as file:
        config.update(json.load(file))

stash_list = []

main_window = tk.Tk()
main_window.title("SSF Pricing")

input_frame = tk.Frame(main_window)
input_frame.pack(pady=2, padx=2, expand=True, fill='both')
ssidvar, accountvar, refvar, privvar = tk.StringVar(), tk.StringVar(), tk.StringVar(), tk.StringVar()

button_frame = tk.Frame(main_window)
button_frame.pack(pady=2, padx=2, expand=True, fill='both')
progress = tk.IntVar()
progress_bar = ttk.Progressbar(button_frame, mode='determinate', variable=progress) 

stash_frame = tk.Frame(main_window)
stash_frame.pack(pady=5, padx=2, expand=True, fill='both')
    
class StashButton:
    def __init__(self, name, index, rgb, id):
        self.name = name
        self.checked = tk.BooleanVar()
        self.hex = '#%02x%02x%02x' % rgb
        self.index = index
        self.id = id
        if self.id in config['preset']:
            self.checked.set(True)
        else:
            self.checked.set(False)
        self.button = tk.Checkbutton(stash_frame, variable=self.checked, text=self.name, bg=self.hex, fg='black', font=20, anchor="w", command=update_preset)

def save_config():
    with open('config.json','w') as file:
        json.dump(config,file)
        
def update_preset():
    for x in stash_list:
        if x.checked.get() and x.id not in config['preset']:
            config['preset'].append(x.id)
        elif not x.checked.get() and x.id in config['preset']:
            config['preset'].remove(x.id)
    save_config()
   
def get_account():
    cookies = {'POESESSID' : config['ssid']}
    headers = {'user-agent' : config['useragent']}
    priv_url = config['priv'].replace(' ','%20')
    url = "https://pathofexile.com/character-window/get-stash-items?league={league}&tabs=1&tabIndex=0&accountName={name}"
    full_url = url.format(league=priv_url,name=config['account'])
    try:
        stash_json = requests.get(full_url,cookies=cookies,headers=headers).json()
        return stash_json
    except:
        return None

def get_stash(index):
    cookies = {'POESESSID' : config['ssid']}
    headers = {'user-agent' : config['useragent']}
    priv_url = config['priv'].replace(' ','%20')
    url = "https://pathofexile.com/character-window/get-stash-items?league={league}&tabs=1&tabIndex={index}&accountName={name}"
    full_url = url.format(league=priv_url,name=config['account'],index=index)
    try:
        stash_json = requests.get(full_url,cookies=cookies,headers=headers).text
        return stash_json
    except:
        return None
    
def create_grid(data):
    global stash_list
    stash_list.clear()
    
    for checkbox in stash_frame.grid_slaves():
        checkbox.grid_forget()
    
    if data:
        tabs_info = data.get('tabs')
        
        col_number = len(tabs_info) // 15 + 1
        for x in range(col_number):
            stash_frame.grid_columnconfigure(x, weight=1)
            
        if tabs_info:
            index = 0
            for tab in tabs_info:
                if "Remove-only" not in tab.get('n'):
                    pos = [index%col_number,index//col_number]
                    colours = tab.get('colour')
                    id = tab.get('id')
                    rgb = (colours.get('r'),colours.get('g'),colours.get('b'))
                    stash_list.append(StashButton(tab.get('n'),index, rgb, id))
                    stash_list[-1].button.grid(column=pos[0],row=pos[1],sticky="wens",padx=5)
                    index += 1
                    
    stash_frame.pack()

def price_one(index):
    poe_data = get_stash(index)
    global progress
    
    if poe_data:
        poe_data_league = poe_data.replace(config['priv'], config['ref'])
        poeprice_url = "https://www.poeprices.info/submitstash"
        dump_data = {'stashitemtext': poe_data_league, 'useML': 'useML', 'auto2': 'auto'}

        x = requests.post(poeprice_url, data=dump_data)
        y = x.text.replace('href="/css', 'href="https://www.poeprices.info/css')
        y = y.replace('src="/css', 'src="https://www.poeprices.info/css')
        y = y.replace('"//', '"https://')
        y = y.replace('/pricestashitem', 'https://www.poeprices.info/pricestashitem')
    
        filename = str(index) + "temp.html"
        with codecs.open(filename, mode="w", encoding='utf-8') as output:
            output.write(y)
        webbrowser.open_new(filename)
        progress_bar.step()
    
def price_checked():
    checked_stash = [x for x in stash_list if x.checked.get()]
    progress_bar['value'] = 0
    progress_bar['maximum'] = len(checked_stash)
    
    threads = []
    for x in checked_stash:
        t = threading.Thread(target=price_one, args=(x.index,))
        t.start()
        threads.append(t)

def create_input():
    ssid = tk.Entry(input_frame, textvariable=ssidvar)
    ssidvar.set(config['ssid'])
    account = tk.Entry(input_frame, textvariable=accountvar)
    accountvar.set(config['account'])
    ref = tk.Entry(input_frame, textvariable=refvar)
    refvar.set(config['ref'])
    priv = tk.Entry(input_frame, textvariable=privvar)
    privvar.set(config['priv'])
    
    ssid.pack(fill='both', expand=True, anchor="w")
    account.pack(fill='both', expand=True, anchor="w")
    ref.pack(fill='both', expand=True, anchor="w")
    priv.pack(fill='both', expand=True, anchor="w")

def create_buttons():
    button_reload = tk.Button(button_frame, text="Reload",command=reload)
    button_price = tk.Button(button_frame,text="Price",command=price_checked)
    
    button_reload.pack(fill='both', expand=True, anchor="w")
    button_price.pack(fill='both', expand=True, anchor="w")
    progress_bar.pack(pady=2, fill='both', expand=True, anchor="w")
    
def reload():
    config.update({'ssid':ssidvar.get(),'account':accountvar.get(),'ref':refvar.get(),'priv':privvar.get()})
    save_config()
    create_grid(get_account())
    
def main():
    create_input()
    create_buttons()
    create_grid(get_account())
    main_window.mainloop()

if __name__ == "__main__":
    main()