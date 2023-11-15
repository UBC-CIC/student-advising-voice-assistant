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

        const description = 
        `The Faculty of Science Advising office at UBC collaborated with the UBC Cloud Innovation Center (CIC) to leverage large language models (LLMs) and generative AI to build a prototype with the goal to improve the advising quality and student experience. 
         The prototype takes information from the Academic Calendar and other reliable UBC sources to provide around-the-clock service that responds to inquiries. 
         The application conveys key information in a conversational manner, in the effort to minimize confusion for some students.
         This application does not require the use of any other software/hardware.
        `;

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
                                name: "student-advising-assistant",
                                summary: "around-the-clock service hosted by UBC, that responds to student's academic inquiries in a conversational manner.",
                                description: description,
                                smallIconUri: "../docs/icons/icon_108_A2Z.png",
                                largeIconUri: "../docs/icons/icon_512_A2Z.png",
                                examplePhrases: ["Alexa, open student advising", "Alexa, start student advising"],
                              }
                            },
                            privacyAndCompliance: {
                                allowsPurchase: false,
                                usesPersonalInfo: false,
                                isChildDirected: false,
                                isExportCompliant: true,
                                shoppingKit: {
                                    isShoppingActionsEnabled: false,
                                    isAmazonAssociatesOnAlexaEnabled: false,
                                },
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