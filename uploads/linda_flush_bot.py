from google.oauth2 import service_account
from googleapiclient.discovery import build

print("Waking up the DriveElite Bot...")
SCOPES = ['https://www.googleapis.com/auth/drive']
creds = service_account.Credentials.from_service_account_file('service_account.json', scopes=SCOPES)
drive_service = build('drive', 'v3', credentials=creds)

print("Scanning the bot's invisible drive for stuck files...")
results = drive_service.files().list(q="'me' in owners", fields="files(id, name)", pageSize=1000).execute()
items = results.get('files', [])

if not items:
    print("✅ The bot's drive is already completely empty!")
else:
    print(f"🚨 Found {len(items)} stuck files! Deleting them now...")
    for item in items:
        print(f"🗑️ Deleting: {item['name']}")
        try:
            drive_service.files().delete(fileId=item['id']).execute()
        except Exception as e:
            print(f"Skipped {item['name']} - {e}")
            
    print("✅ Bot flushed! All storage is freed up.")
