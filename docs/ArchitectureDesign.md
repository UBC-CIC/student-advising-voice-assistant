# Architecture Design #

This document provides a more in-depth explanation of the system's architecture and operation.

## Table of Contents ## 
- [Introduction](#introduction)
- [Architecture Diagram](#architecture-diagram)

## Introduction ##

This voice assistant feature is designed for [Student Advising Assistant](https://github.com/UBC-CIC/student-advising-assistant) project.  

## Architecture Diagram ##
![diagram](./images/Architecture-Diagram.png)

**Question Answering**  
1. User asks a question to the Alexa-integrated device.  
2. Alexa first converts voice to text, uses Natural Language Understanding(NLU) to interpret user's question and calls an appropriate handler to generate the answer for the question.
3. AWS Lambda function acts as a request handler, and calls the API defined in the Student Advising project to retrieve the answer. To find out more about how the response is generated, you can find the information [here](https://github.com/UBC-CIC/student-advising-assistant/blob/main/docs/ArchitectureDesign.md#aws-infrastructure).
4. Generated response is sent back from Student Advising Assistant to Lambda handler. 
5. Lambda receives the answer as a HTTP response. Then it sends it directly to Alexa Skills in JSON format.
6. Alexa interprets the response, converts text to voice, and speaks the answer back to the user. 