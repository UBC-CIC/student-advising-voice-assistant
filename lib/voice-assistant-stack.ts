import { Stack, StackProps } from 'aws-cdk-lib';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as ask from 'cdk-skill-management';
import * as ssm from 'aws-cdk-lib/aws-ssm';
import * as secretsmanager from 'aws-cdk-lib/aws-secretsmanager';
import { Asset } from 'aws-cdk-lib/aws-s3-assets';
import { Construct } from 'constructs';

export class VoiceAssistantStack extends Stack {

    constructor(scope: Construct, id: string, props?: StackProps) {

        super(scope, id, props);

        new ssm.StringParameter(this, 'vendor-parameter', {
            parameterName: "my-skill-vendor-id",
            stringValue: "M33ZTT1LFMTQJS",
        });

        const cliendId = secretsmanager.Secret.
            fromSecretCompleteArn(this, 'client-id-parameter', 'arn:aws:secretsmanager:ca-central-1:286997668524:secret:client-id-8NfJxZ');
        const clientSecret = secretsmanager.Secret.
            fromSecretCompleteArn(this, 'client-secret-parameter', 'arn:aws:secretsmanager:ca-central-1:286997668524:secret:client-secret-ELwxWq');
        const refreshToken = secretsmanager.Secret.
            fromSecretCompleteArn(this, 'refresh-token-parameter', 'arn:aws:secretsmanager:ca-central-1:286997668524:secret:refresh-token-plain-OakLG3');

        const skillAsset = new Asset(this, 'skill-asset', {
            path: './skills/skill-package',
        });

        const skillBackendLayer = new lambda.LayerVersion(this, 'skill-backend-layer', {
            code: lambda.Code.fromAsset('./layers/skill_backend_layer.zip'),
            compatibleRuntimes: [lambda.Runtime.PYTHON_3_9],
        })

        const skillBackend = new lambda.Function(this, 'skill-backend', {
            runtime: lambda.Runtime.PYTHON_3_9,
            code: lambda.Code.fromAsset('./lambda'),
            handler: 'voice_assistant.lambda_handler',
            layers: [skillBackendLayer],
        });

        const skillPermission = new ask.SkillEndpointPermission(this, 'skill-permission', {
            handler: skillBackend,
            skillType: ask.SkillType.CUSTOM,
        });

        const skill = new ask.Skill(this, 'skill', {
            skillType: ask.SkillType.CUSTOM,
            skillStage: 'development',
            vendorId: 'M33ZTT1LFMTQJS',
            authenticationConfiguration: {
                clientId: cliendId.secretValue.unsafeUnwrap(),
                clientSecret: clientSecret.secretValue.unsafeUnwrap(),
                refreshToken: refreshToken.secretValue.unsafeUnwrap(),
            },
            skillPackage: {
                asset: skillAsset,
                overrides: {
                    manifest: {
                        apis: {
                            custom: {
                                endpoint: {
                                    uri: skillBackend.functionArn
                                }
                            }
                        },
                        publishingInformation: {
                            locales: {
                              "en-CA": {
                                name: "student-advising-assistant"
                              }
                            },
                            category: "EDUCATION_AND_REFERENCE"
                          }
                    }
                }
            },
        });
        skill.node.addDependency(skillBackend);
        skill.node.addDependency(skillPermission);

        // skillPermission.configureSkillId(this, 'skill-permission-id', skill);
    }
}