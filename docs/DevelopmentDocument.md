# Development Document #

This document will go over some of the implementation details of this application.

## Table of Contents ##
- [Developing Alexa Skill](#developing-alexa-skill)
    - [Alexa Skills Kit for python](#alexa-skills-kit-for-python)
    - [Dynamic Entity](#dynamic-entity)
    - [Progressive Response](#progressive-response)

## Developing Alexa Skill

The key component of this application is Alexa Skill, which is a voice activated application that runs on Alexa-enabled devices. Alexa Skills can be developed with a software development framework called **Alexa SKills Kit (ASK)**.   
Alexa utilizes its Automated Speech Recognition system to interpret the user's intent, and fulfill it by interacting with the backend services, such as AWS Lambda functions or HTTPS endpoints. 

### Alexa Skills Kit for Python ###
For this application, Python is used in the backend services. To develop an Alexa Skill with Python, we used the standard SDK package for Alexa SKills Kit called [ask-sdk](https://pypi.org/project/ask-sdk/). This makes it easier to build highly engaging skills by allowing developers to spend less time on writing boilerplate code.

### Dynamic Entity ###
In this application, users are required to specify their faculty and program before asking any question, as well as their specialization and/or year level when asking program-specific questions. 

The options for those fields depends on the user's previous response. For example, if the user is in the Faculty of Science, the program choices are restricted to those listed under the Faculty of Science.   
In order to dynamically create the options to any query, this application utilizes the **dynamic entity** feature provided by Alexa Skills Kit. 

"Dynamic entity" allows the application to dynamically create new entities in runtime. This means that the user interface will automatically update itself based on Alexa's conversations with the user. 

### Progressive Response ###
As mentioned in [architecture design](./ArchitectureDesign.md), the application retrieves the answer from the Student Advising Assistant project by making a HTTP request. However, this process takes approximately 10-15 seconds, which is slightly longer than the time Alexa keeps the session open and waits for the response after recording the user's input. 

To keep Alexa's session open while preparing for the full response, this application utilizes the **progressive response** feature of the Alexa Skills Kit.

"Progressive response" is interstitial text-to-speech content that Alexa plays while waiting for the full response from the backend. This application uses progressive responses to do the following tasks:
- Send confirmation that the application has received the request(intput) from the user.
- Reduce the user's perception of latency in the application's response. 
