import { defineAuth } from '@aws-amplify/backend';

/**
 * Define and configure your auth resource
 * @see https://docs.amplify.aws/gen2/build-a-backend/auth
 */
/*
export const auth = defineAuth({
  loginWith: {
    email: true,
  },
});
*/
import { referenceAuth } from '@aws-amplify/backend';

export const auth = referenceAuth({
  userPoolId: 'us-west-2_KvNDBMljE',
  identityPoolId: 'us-west-2:c839acd7-81ed-4266-8776-89068288760c',
  authRoleArn: 'arn:aws:iam::400142384867:role/amplify-aiimagegenerator--amplifyAuthauthenticatedU-5UcaIX9mkIJt',
  unauthRoleArn: 'arn:aws:iam::400142384867:role/amplify-aiimagegenerator--amplifyAuthunauthenticate-6JRbcnEFiciR',
  userPoolClientId: '6sc0nqta7a2kt727shji0qqeen',
});