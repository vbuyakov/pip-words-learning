


# 🚀 Setup Steps for Firebase + Firestore

## *1.* Create a Firebase Project
1. Go to [Firebase Console](https://console.firebase.google.com/).
2. Click **"Add Project"** and follow the setup instructions.
3. Enable **Firestore Database**:
   - Navigate to **Build** → **Firestore Database**.
   - Click **"Create Database"**.
   - Select **"Start in test mode"** (for now).
   - Choose your **Cloud Firestore location** and confirm.

---

## *2.* Get Firebase Credentials
1. Go to **Project Settings** (⚙️ in the top-left).
2. Click the **"Service Accounts"** tab.
3. Select **"Generate new private key"**.
4. Download the generated **`firebase_credentials.json`** file.
5. Move the file into your project directory.

---

## *3.* Prepare OpenAI API
To generate you own vocabulary we use OpenAI API. To do this create openAI tocken 
then copy config_example.json to config.json and set openai_api_key parameter
If you you don't wont to genereate you own lists to learning you can skip this step

```bash
cp config_example.json config.json 
```




## *4.* Install Required Tools

### ✅ Install Required Python Packages
```bash
pip install -r requirements.txt
```


---

## *4.* Running the Project
Ensure you are in the project directory and run:
```bash
python learnelectro.py
```

