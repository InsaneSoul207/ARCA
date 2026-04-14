import os
 
APP_NAME = "ACRA"
VERSION  = "MVP-1.0  |  Windows"
 
BASE_DIR      = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH    = os.path.join(BASE_DIR, "models", "intent_model.pkl")
INTENTS_JSON  = os.path.join(BASE_DIR, "models", "intents.json")   
LOG_PATH      = os.path.join(BASE_DIR, "alpha_log.txt")
NOTES_PATH    = os.path.join(BASE_DIR, "alpha_notes.txt")
 
ENERGY_THRESHOLD    = 200     
PAUSE_THRESHOLD     = 0.7    
PHRASE_TIME_LIMIT   = 12      
DYNAMIC_ENERGY      = True    
 
WAKE_WORD = "alpha"         
 
MAX_SEQUENCE_LEN = 28         
EMBEDDING_DIM    = 128        
HIDDEN_DIM       = 256        
EPOCHS           = 50       
LEARNING_RATE    = 0.001      

FULL_W, FULL_H       = 900, 700   
COMPACT_W, COMPACT_H = 360, 160 
 
BG_BASE  = "#050505"    
BG_PANEL = "#0D0D0D"    
BG_DEEP  = "#121212"    
BG_GLASS = "#1A1A1A"    

ACCENT  = "#00D4FF"    
ACCENT2 = "#008FB3"    
ACCENT3 = "#6E3FFF"    

# Text
TEXT_DARK  = "#FFFFFF"  
TEXT_MID   = "#E0E0E0"  
TEXT_DIM   = "#888888"  
TEXT_GHOST = "#333333" 

GREEN  = "#00C48C"     
RED    = "#FF3B5C"      
YELLOW = "#FFB800"      
ORANGE = "#FF6B2B"    

BORDER      = "#1F1F1F"  
BORDER_GLOW = "#00D4FF"

FONT_TITLE  = ("Consolas", 22, "bold")  
FONT_HEAD   = ("Consolas", 11, "bold")   
FONT_BODY   = ("Consolas", 10)
FONT_SMALL  = ("Consolas",  9)       
FONT_MICRO  = ("Consolas",  8)          
FONT_LOG    = ("Consolas",  8)        
FONT_COMPACT= ("Consolas",  8)    


CONTACTS={"eshaan" : "+918920512631", "mom":"+919873007432","mum":"+919873007432","dad":"+919999757862","aadityasuri":"+919667762563","aakanshBaghel":"+918115198893",
"aman":"+919899177921","amogh":"+916390134070","anshdixit":"+919311053949","anshgarg":"+919310057049","anushka":"+919411776110","anveshmishra":"+919457740019",
"arush":"+918527282060","atharvashah":"+918005698214","chaitanyasharma":"+918287036781","bhoomichauhan":"+918920165398","dhruvtaliyan":"+916395251516",
"divyanshi":"+918630670854","saurabhsir":"+919910364680","gitali":"+919234075485","harsh":"+919315507269","harshvardhansingh":"+917898182921","kunsh":"+919625218815",
"mainak":"+918436986507","muditagrawal":"+917267898789","mystery":"+918287319613","omnegi":"+919266148718","ojasvats":"+919311156738","plainaditya":"+918054214889",
"prachimam":"+917378715067","pratham":"+919310811749","priyanshu":"+918709077479","sahilveergauto":"+919643995769","sanchit":"+919084180090",
"shreya":"+918144963396","snehasingh":"+919682327558","tanusomani":"+919335308115","tanvigoyal":"+918882214741","timonne":"+918287258567","utkarshhhwaliahos":"+917417393838",
"vijendra":"+917878086942", "vivek": "+917579281667"}