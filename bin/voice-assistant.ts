#!/usr/bin/env node
import 'source-map-support/register';
import * as cdk from 'aws-cdk-lib';
import { VoiceAssistantStack } from '../lib/voice-assistant-stack';

const app = new cdk.App();
cdk.Tags.of(app).add("Application", "Student Advising Voice Assistant");

new VoiceAssistantStack(app, 'VoiceAssistantStack', {});

