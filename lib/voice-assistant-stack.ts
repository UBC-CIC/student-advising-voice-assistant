import { Stack, StackProps } from 'aws-cdk-lib';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as ask from 'cdk-skill-management';
import * as secretsmanager from 'aws-cdk-lib/aws-secretsmanager';
import { Asset } from 'aws-cdk-lib/aws-s3-assets';
import { Construct } from 'constructs';

export class VoiceAssistantStack extends Stack {

    constructor(scope: Construct, id: string, props?: StackProps) {

        super(scope, id, props);

        /*
            Please replace the value below with the ARN of the secret you created earlier.
            Do not remove the quotation marks ('').
        */
        const secretARN = 'XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX';

        const skillCredentials = secretsmanager.Secret.fromSecretCompleteArn(this, 'skill-credentials', secretARN);

        const skillAsset = new Asset(this, 'skill-asset', {
            path: './skills/skill-package',
        });

        const skillBackendLayer = new lambda.LayerVersion(this, 'skill-backend-layer', {
            code: lambda.Code.fromAsset('./layers/skill_backend_layer.zip'),
            compatibleRuntimes: [lambda.Runtime.PYTHON_3_11],
        })

        const skillBackend = new lambda.Function(this, 'skill-backend', {
            runtime: lambda.Runtime.PYTHON_3_11,
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
            vendorId: skillCredentials.secretValueFromJson('vendor-id').unsafeUnwrap(),
            authenticationConfiguration: {
                clientId: skillCredentials.secretValueFromJson('client-id').unsafeUnwrap(),
                clientSecret: skillCredentials.secretValueFromJson('client-secret').unsafeUnwrap(),
                refreshToken: skillCredentials.secretValueFromJson('refresh-token').unsafeUnwrap(),
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
                            category: "EDUCATION_AND_REFERENCE"
                        }
                    }
                }
            },
        });
        skill.node.addDependency(skillBackend);
        skill.node.addDependency(skillPermission);
    }
}