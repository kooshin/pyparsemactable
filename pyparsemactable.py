#!/usr/bin/env python
# 
# Copyright (c) 2021 @kooshin
#

import re
import tkinter as tk
from tkinter.scrolledtext import ScrolledText

default_show_mac_address_table = """\
sw2#show mac address-table 
          Mac Address Table
-------------------------------------------

Vlan    Mac Address       Type        Ports
----    -----------       --------    -----
   1    5254.000d.490f    DYNAMIC     Gi1/0
 101    0000.5e00.0165    DYNAMIC     Gi1/0
 101    5254.0007.f67c    DYNAMIC     Gi1/0
 101    5254.000d.a28a    DYNAMIC     Gi0/0
 102    0000.5e00.0166    DYNAMIC     Gi1/0
 102    0000.5e00.0266    DYNAMIC     Gi1/0
 102    5254.000f.8ec5    DYNAMIC     Gi1/0
 102    5254.001c.f778    DYNAMIC     Gi0/1
 103    0000.0c07.ac67    DYNAMIC     Gi1/0
 103    5254.0008.6325    DYNAMIC     Gi1/0
 103    5254.001b.edff    DYNAMIC     Gi0/2
 104    0000.0c9f.f068    DYNAMIC     Gi1/0
 104    0005.73a0.0069    DYNAMIC     Gi1/0
 104    5254.0008.793c    DYNAMIC     Gi0/3
 104    5254.0008.7a83    DYNAMIC     Gi1/0
Total Mac Addresses for this criterion: 15
"""

class ParseMacTableApp(tk.Frame):
    def __init__(self, master=None):
        super().__init__(master)
        self.master = master
        self.pack(expand=True, fill=tk.BOTH)
        self.create_widgets()


    def create_widgets(self):
        self.input_label = tk.Label(self, text="入力欄：show mac address-tableの結果を下記に貼り付けてください", anchor=tk.W)
        self.input_label.pack(fill=tk.BOTH)

        self.input_box = ScrolledText(self, height=10)
        self.input_box.pack(expand=True, fill=tk.BOTH)
        self.input_box.insert(1.0, default_show_mac_address_table)

        self.parse_button = tk.Button(self, text="抽出", command=self.parse_input)
        self.parse_button.pack()

        self.output_label = tk.Label(self, text="実行結果", anchor=tk.W)
        self.output_label.pack(fill=tk.BOTH)

        self.output_box = ScrolledText(self, height=20)
        self.output_box.pack(expand=True, fill=tk.BOTH)

        self.parse_button = tk.Button(self, text="クリップボードからコピー＆ペースト", command=self.parse_input_from_clipboard)
        self.parse_button.pack()

        self.parse_input()


    def parse_input_from_clipboard(self):
        self.input_box.delete(1.0, tk.END)
        try:
            self.input_box.insert(1.0, self.clipboard_get())
            self.parse_input()
            output_text = self.output_box.get(1.0, tk.END)
            self.clipboard_clear()
            self.clipboard_append(output_text)
        except Exception as e:
            self.input_box.insert(1.0, f"{e}")


    def parse_input(self):
        input_text = self.input_box.get(1.0, tk.END)
        output_text = self.parse_mac_address(input_text)
        self.output_box.delete(1.0, tk.END)
        self.output_box.insert(1.0, output_text)


    def parse_mac_address(self, mac_table):
        results = "vlan,mac_address,type,ports,group_protocol,group_number\r\n"
        matches = re.finditer(
            r"^\s*(?P<vlan>\d+)\s+(?P<mac>[0-9a-f]{4}\.[0-9a-f]{4}\.[0-9a-f]{4})\s+(?P<type>\S+)\s+(?P<ports>\S+)",
            mac_table,
            flags=re.MULTILINE | re.IGNORECASE
        )
        for match in matches:
            vlan = match.group("vlan")
            mac_address = match.group("mac")
            mac_type = match.group("type")
            ports = match.group("ports")

            # MAC Address       FHRP Protocol/IP Version
            # 0000.5e00.01XX    VRRP IPv4
            # 0000.5e00.02XX    VRRP IPv6
            # 0000.0c07.acXX    HSRPv1 IPv4
            # 0000.0c9f.fXXX    HSRPv2 IPv4
            # 0005.73a0.0XXX    HSRPv2 IPv6
            vrrp_v4_match = re.match(r"0000\.5e00\.01([0-9a-f]{2})", mac_address, flags=re.IGNORECASE)
            vrrp_v6_match = re.match(r"0000\.5e00\.02([0-9a-f]{2})", mac_address, flags=re.IGNORECASE)
            hsrpv1_v4_match = re.match(r"0000\.0c07\.ac([0-9a-f]{2})", mac_address, flags=re.IGNORECASE)
            hsrpv2_v4_match = re.match(r"0000\.0c9f\.f([0-9a-f]{3})", mac_address, flags=re.IGNORECASE)
            hsrpv2_v6_match = re.match(r"0005\.73a0\.0([0-9a-f]{3})", mac_address, flags=re.IGNORECASE)
            
            group_protocol = ""
            group_number = ""   
            if vrrp_v4_match:
                group_protocol = "VRRPv2/v3(IPv4)"
                group_number = int(vrrp_v4_match.group(1), 16)
            elif vrrp_v6_match:
                group_protocol = "VRRPv3(IPv6)"
                group_number = int(vrrp_v6_match.group(1), 16)
            elif hsrpv1_v4_match:
                group_protocol = "HSRPv1(IPv4)"
                group_number = int(hsrpv1_v4_match.group(1), 16)
            elif hsrpv2_v4_match:
                group_protocol = "HSRPv2(IPv4)"
                group_number = int(hsrpv2_v4_match.group(1), 16)
            elif hsrpv2_v6_match:
                group_protocol = "HSRPv2(IPv6)"
                group_number = int(hsrpv2_v6_match.group(1), 16)

            results += f"{vlan},{mac_address},{mac_type},{ports},{group_protocol},{group_number},\r\n"

        return results

if __name__ == "__main__":
    root = tk.Tk()
    root.title("VRRP/HSRPグループ番号抽出")
    app = ParseMacTableApp(master=root)
    app.mainloop()
