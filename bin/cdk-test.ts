#!/usr/bin/env node
import 'source-map-support/register';
import * as cdk from 'aws-cdk-lib';
import { VoiceAssistantStack } from '../lib/voice-assistant-stack';

const app = new cdk.App();

new VoiceAssistantStack(app, 'VoiceAssistantStack', {});
