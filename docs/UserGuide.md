# User Guide #
**Before continuing with this User Guide, please make sure you have deployed the application.**
- [Deployment Guide](./DeploymentGuide.md)

| Index | Description |
| ----- | ----------- |
| [Local Computer](#local-computer) | How to test the behavior of the application in Alexa Developer Console |
| [Alexa Devices](#alexa-devices) | How to use the voice assistant on Alexa devices | 
| [Publish Your Skill](#publish-your-skill) | How to publish your Alexa Skill |

## Local Computer ##
You will be able to test out the behavior of the application on [Alexa Developer Console](https://developer.amazon.com/alexa/console/ask).   
When you log into the console, you should see a skill named `student-advising-assistant`.![ask-console](./images/ask_console.png)
From the `ACTIONS` dropdown menu on the right, choose `Test` and proceed.

![console-test](./images/ask_console_test.png)
You will be navigated to this console.  
Select `Development` in the top-left dropdown menu, and you can now start testing out the behavior.  
The left section of the console shows the interaction dialogs. Please type in `open student advising` to invoke the skill and start the conversation with Alexa. 

## Alexa Devices ##

**Now it's time to test your skill on Alexa-integrated device!**  

At this point, you can only use your skill on Alexa devices associated with your Amazon Developer account. Therefore, when you set up the device please sign in with your Amazon Developer account.

After you sign in with you account, you can start using the skill by saying `Alexa, open student advising`. 

## Publish Your Skill ##
At this point, your voice assistant application can only be used in Alexa devices associated with your Amazon Developer account. To make it available for anyone, **you will need to publish your Alexa skill to Alexa skill store**.

To publish your skill, go to [Alexa Developer Console](https://developer.amazon.com/alexa/console/ask), log in if needed, choose your skill and click `Certification` from the top menu bar.

![certification](./images/ask_certification.png)  
Your screen should look like the screenshot above. 

Then, click `Submission` menu from the side bar and click `Submit for review` to submit your skill for approval.   
Once your skill passes the certification, you will be given a link. You can share it with other users so that they can enable your skill and use it in their Echo device.