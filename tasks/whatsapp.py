import pywhatkit
import time
from config import CONTACTS
from core.speaker import speak
try:
    from core.logger import log
except ImportError:
    def log(msg, level="INFO"):
        print(f"[{level}] {msg}")

CONTACTS={"eshaan" : "+918920512631", "mom":"+919873007432","mum":"+919873007432","dad":"+919999757862","aadityasuri":"+919667762563","aakanshBaghel":"+918115198893",
"aman":"+919899177921","amogh":"+916390134070","anshdixit":"+919311053949","anshgarg":"+919310057049","anushka":"+919411776110","anveshmishra":"+919457740019",
"arush":"+918527282060","atharvashah":"+918005698214","chaitanyasharma":"+918287036781","bhoomichauhan":"+918920165398","dhruvtaliyan":"+916395251516",
"divyanshi":"+918630670854","saurabhsir":"+919910364680","gitali":"+919234075485","harsh":"+919315507269","harshvardhansingh":"+917898182921","kunsh":"+919625218815",
"mainak":"+918436986507","muditagrawal":"+917267898789","mystery":"+918287319613","omnegi":"+919266148718","ojasvats":"+919311156738","plainaditya":"+918054214889",
"prachimam":"+917378715067","pratham":"+919310811749","priyanshu":"+918709077479","sahilveergauto":"+919643995769","sanchit":"+919084180090",
"shreya":"+918144963396","snehasingh":"+919682327558","tanusomani":"+919335308115","tanvigoyal":"+918882214741","timonne":"+918287258567","utkarshhhwaliahos":"+917417393838",
"vijendra":"+917878086942", "vivek": "+917579281667"}

def send_whatsapp_message(contact_name, message, headless=False):

    name_lower = contact_name.lower().strip()
    if name_lower not in CONTACTS:
        error_msg = f"I couldn't find a number for '{contact_name}' in your contacts dictionary."
        log(error_msg, "WARN")
        return error_msg
    
    phone_num = CONTACTS[name_lower]
    
    try:
        log(f"Opening browser to WhatsApp {contact_name} ({phone_num})...", "INFO")
        
        pywhatkit.sendwhatmsg_instantly(
            phone_no=phone_num, 
            message=message, 
            wait_time=15, 
            tab_close=True, 
            close_time=3
        )
        
        success_msg = f"Message successfully sent to {contact_name}."
        log(success_msg, "INFO")
        return success_msg
        
    except Exception as e:
        error_msg = f"Pywhatkit failed to send the message. Error: {e}"
        log(error_msg, "ERROR")
        return error_msg

if __name__ == "__main__":
    contact = "Eshaan"
    msg = "Testing ARCA with the new pywhatkit module!"
    print(send_whatsapp_message(contact, msg))