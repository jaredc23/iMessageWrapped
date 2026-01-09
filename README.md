# iMessages Wrapped

This is an application that can be used to get the iMessage information off of your phone and then display a 2025 wrapped for it!

## Demo

The sample file so you don't need to backup your phone to open the app is inside Release 1.0/sample_wrapped_2025.imsgwrp

The screenshots below show the app UI. Click an image to open the full-size version.

<table>
    <tr>
        <td align="center"><a href="Sample Images/1-Home Page.png"><img src="Sample Images/1-Home Page.png" alt="Home Page" width="300"/></a></td>
        <td align="center"><a href="Sample Images/2-Words Per Text.png"><img src="Sample Images/2-Words Per Text.png" alt="Words Per Text" width="300"/></a></td>
        <td align="center"><a href="Sample Images/3-Top Convo.png"><img src="Sample Images/3-Top Convo.png" alt="Top Convo" width="300"/></a></td>
    </tr>
    <tr>
        <td align="center"><a href="Sample Images/4-Top Convos.png"><img src="Sample Images/4-Top Convos.png" alt="Top Convos" width="300"/></a></td>
        <td align="center"><a href="Sample Images/5-Top Chats.png"><img src="Sample Images/5-Top Chats.png" alt="Top Chats" width="300"/></a></td>
        <td align="center"><a href="Sample Images/6-Response Time.png"><img src="Sample Images/6-Response Time.png" alt="Response Time" width="300"/></a></td>
    </tr>
    <tr>
        <td align="center"><a href="Sample Images/7-Top emoji.png"><img src="Sample Images/7-Top emoji.png" alt="Top Emoji" width="300"/></a></td>
        <td align="center"><a href="Sample Images/8-Emoji timeline.png"><img src="Sample Images/8-Emoji timeline.png" alt="Emoji Timeline" width="300"/></a></td>
        <td align="center"><a href="Sample Images/9-Attachments.png"><img src="Sample Images/9-Attachments.png" alt="Attachments" width="300"/></a></td>
    </tr>
    <tr>
        <td align="center"><a href="Sample Images/A-Message Timeline.png"><img src="Sample Images/A-Message Timeline.png" alt="Message Timeline" width="300"/></a></td>
        <td align="center"><a href="Sample Images/B-Texts by Hour.png"><img src="Sample Images/B-Texts by Hour.png" alt="Texts by Hour" width="300"/></a></td>
        <td align="center"><a href="Sample Images/C-Summary.png"><img src="Sample Images/C-Summary.png" alt="Summary" width="300"/></a></td>
    </tr>
</table>

*Tip:* click any image to view it at full size; thumbnails are limited to 300px wide for readability.

Due to Apple's restrictions on iMessages, unfortunately it is quite difficult to get the information off of your phone and therefore requires a few manual command line steps in order to get it to work fully.

The basic order of operations is

1. Backup your phone (This can't read an encrypted backup, so don't use encryption but, MAKE SURE TO DELETE IT WHEN DONE) (Backup your phone through Finder or idevicebackup2). (Don't encrypt the backup, use: `idevicebackup2 backup --full /location/of/backup`)
2. Use executables in this repo to
    * Extract the necessary databases from your backup
    * Parse those databases to create the necessary files
    * You can at this point manually go in an disable some chats from being used
    * Generated the final .msgwrp Wrapped file
3. Open the native Mac application (Compatible for Intel and Apple silicon) to open and display the .msgwrp file

## Setup

### Backup phone
The first thing that you will need is an iphone backup. This can be done in finder, and it will backup to the default location on your computer. You should find that location and save it because it will be used later. Or you can use the terminal `idevicebackup2 backup --full /location/of/backup`

Make sure not to encrypt the backup. For safety, you should delete the backup once you are done.

### Get the chat and contacts databases from your backup

Create a directory that you will use to store your data. It can be anywhere such as your Desktop for example.

Copy in the three executables (in Release 1.0 folder) into the directory you just created(iPhoneBackup, MessageParser, MessagesWrapped)

Then run the following executable:

```
./iPhoneBackup extract --output-dir="./" --password="" --backup-dir="<Location of your backup>"
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
