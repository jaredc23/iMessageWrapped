# iMessages Wrapped

## Setup

### Backup phone
The first thing that you will need is an iphone backup. This can be done in finder, and it will backup to the default location on your computer. You should find that location and save it because it will be used later.

NOTE: you will need to password encrypt your backup. Make sure that you save that password, it will need to be used

### Get the chat and contacts databases from your backup

Create a directory that you will use to store your data. It can be anywhere such as your Desktop for example.

Copy in the three executables (in Backend/dist/) into the directory you just created(iPhoneBackup, MessageParser, MessagesWrapped)

Then run the following executable:

```
./iPhoneBackup extract --output-dir="./" --password="<Password used>" --backup-dir="<Location of your backup>"
```

Then it will spit out two files: a chat.db file and a contacts.db file. If it is named differently, make sure to rename it to that.

### Parse the databases and create your chat files

This step is what actually reads the data and spits out the chats which will be used to generate the statistics

```
./MessageParser --sms-db-path="./chat.db" --contacts-db-path="./contacts.db" --output-dir="./"
```

This should leave a lot of chat*.json files in your directory

### Edit the chats you want to include

In the directory it will spit out a file `number_to_name.json`. This file has every chat from your phone with an "include" option with it. Some chats are default false, which are the chats with no messages this year and the chats with only unsaved contacts. You can go into this file manually and disable chats you don't want to include in the statistics

### Create the final wrapped file

This step will be the final preparation step, it will spit out the final file called "wrapped_2025.json".

NOTE: This step takes the longest! It can take from minutes to hours

```
./MessagesWrapped --exports-dir="./" --max-workers="4"
```

This will spit out a file called `wrapped_2025.imsgwrp`. This is the file that will be used in the application to display the data