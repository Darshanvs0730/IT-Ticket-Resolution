import os
import sys
from datetime import datetime, timedelta
import random

# Add parent directory to path so we can import 'app'
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import engine, Base, SessionLocal
from app.models import HistoricalTicket

def seed_database():
    # Attempt to create tables if they don't exist
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    
    # Check if we already have data
    if db.query(HistoricalTicket).count() > 0:
        print("Database already seeded with historical tickets.")
        db.close()
        return

    print("Seeding ~50 synthetic historical tickets into the database...")

    templates = [
        # Hardware
        {"title": "Laptop won't turn on", "description": "My company-issued laptop is completely dead. Pushing the power button does nothing.", "category": "Hardware", "resolution": "Instructed user to hold the power button for 30s to hard reset the battery. The device then booted normally."},
        {"title": "Printer not responding", "description": "HP LaserJet in room 204 won't print my document.", "category": "Hardware", "resolution": "Restarted the print spooler service on the user's machine and cleared the printer queue physically. Printed test page successfully."},
        {"title": "External monitor flickering", "description": "The second screen randomly goes black and comes back.", "category": "Hardware", "resolution": "Swapped the HDMI cable and updated the display drivers via Windows Update."},
        {"title": "Keyboard keys sticking", "description": "The spacebar and enter key keep getting stuck when I type.", "category": "Hardware", "resolution": "Provided the user with a replacement keyboard from IT inventory."},
        {"title": "Mouse tracking erratically", "description": "The wireless mouse cursor jumps around the screen.", "category": "Hardware", "resolution": "Replaced the batteries and cleaned the optical sensor with microfiber."},
        
        # Software
        {"title": "Excel keeps crashing", "description": "Every time I open a large spreadsheet, Excel freezes and closes.", "category": "Software", "resolution": "Disabled conflicting COM Add-ins (specifically the PDF maker add-in) and repaired Office installation."},
        {"title": "Teams not loading", "description": "Microsoft Teams is stuck on the loading splash screen.", "category": "Software", "resolution": "Cleared the Teams AppData cache folder and restarted the application."},
        {"title": "Can't install application", "description": "I need Adobe Acrobat installed but it asks for admin rights.", "category": "Software", "resolution": "Remoted into the machine, verified the software request approval, and inputted IT admin credentials to complete the installation."},
        {"title": "Outlook search not working", "description": "When I search for an email, it says 'We couldn't find what you were looking for'.", "category": "Software", "resolution": "Rebuilt the Windows Search index specifically for Microsoft Outlook data files."},
        {"title": "Browser running slow", "description": "Google Chrome takes forever to load any internal intranet page.", "category": "Software", "resolution": "Cleared browsing data (cache/cookies) and disabled heavily resource-intensive extensions."},
        
        # Network
        {"title": "VPN connection failed", "description": "Cisco AnyConnect gives an error when connecting from home.", "category": "Network", "resolution": "Updated the VPN client to the latest version and instructed the user to reconnect to their Wi-Fi."},
        {"title": "Wi-Fi is dropping", "description": "My laptop disconnects from the corporate office Wi-Fi every 10 minutes.", "category": "Network", "resolution": "Updated the wireless network adapter drivers and reset the winsock catalog."},
        {"title": "Can't access shared drive", "description": "The Z: drive is showing a red X and I can't browse the finance folder.", "category": "Network", "resolution": "Re-mapped the network drive using the new server IP and verified user permissions in Active Directory."},
        {"title": "Intranet page timeout", "description": "The HR portal is not loading, it just spins and times out.", "category": "Network", "resolution": "Flushed DNS cache on the client machine and verified the proxy configuration in Internet Options."},
        {"title": "Slow download speed", "description": "Downloading the marketing video is taking 3 hours.", "category": "Network", "resolution": "User was connected to the guest Wi-Fi. Switched them to the wired corporate LAN for better bandwidth."},

        # Access
        {"title": "Account locked out", "description": "I entered my password wrong too many times and now I'm locked out.", "category": "Access", "resolution": "Unlocked the user's Active Directory account and helped them reset their password via the self-service portal."},
        {"title": "Need access to Jira", "description": "I joined the new project but I don't have access to the Jira board.", "category": "Access", "resolution": "Added the user to the proper Active Directory security group for the Jira project."},
        {"title": "MFA token not working", "description": "The authenticator app codes are failing to let me log in.", "category": "Access", "resolution": "Re-synchronized the MFA token's time settings in the app and issued a temporary bypass code."},
        {"title": "Password reset required", "description": "My password expired and I am working remotely.", "category": "Access", "resolution": "Guided user to the VPN pre-login password reset tool to update credentials remotely."},
        {"title": "Can't login to Salesforce", "description": "Salesforce says invalid login. SSO isn't working.", "category": "Access", "resolution": "Found a stale SSO session. Instructed user to clear browser cookies and try again via the Okta dashboard."},
        
        # Additional Mix
        {"title": "Blue screen of death", "description": "My computer randomly showed a blue screen with an error code and rebooted.", "category": "Hardware", "resolution": "Analyzed minidump file. The issue was a faulty RAM stick. Replaced RAM and ran memtest."},
        {"title": "Audio not working on calls", "description": "People can't hear me in Zoom meetings.", "category": "Hardware", "resolution": "Checked Windows sound settings. The microphone was disabled in privacy settings. Re-enabled it."},
        {"title": "Zoom update failed", "description": "Zoom is prompting for an update but fails halfway through.", "category": "Software", "resolution": "Uninstalled the old version completely and ran the standalone MSI installer for the latest version."},
        {"title": "Lost my phone", "description": "I misplaced my company mobile device and need it secured.", "category": "Other", "resolution": "Issued a remote wipe command via the MDM console and flagged the device as lost in inventory."},
        {"title": "Need a software license", "description": "I need Visio for a diagram I have to make.", "category": "Other", "resolution": "Verified manager approval, allocated an available license in the Microsoft 365 Admin Center, and confirmed installation."}
    ]

    base_date = datetime.utcnow() - timedelta(days=365)
    
    historical_tickets = []
    # Replicate to get ~50 tickets, slight variations
    for i in range(2):
        for template in templates:
            ticket = HistoricalTicket(
                title=template["title"] if i == 0 else template["title"] + " (Similar)",
                description=template["description"] + (" Urgent issue." if i == 1 else ""),
                category=template["category"],
                resolution_text=template["resolution"],
                resolved_at=base_date + timedelta(days=random.randint(1, 360)),
                similarity_score=random.uniform(0.7, 0.99),
                times_matched=random.randint(0, 10)
            )
            historical_tickets.append(ticket)
            
    db.bulk_save_objects(historical_tickets)
    db.commit()
    db.close()
    print(f"Successfully seeded {len(historical_tickets)} historical tickets.")

if __name__ == "__main__":
    seed_database()
