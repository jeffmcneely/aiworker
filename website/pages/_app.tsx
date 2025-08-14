import type { AppProps } from 'next/app'
import '../styles/globals.css'
import '@aws-amplify/ui-react/styles.css'
import { Amplify } from 'aws-amplify'

// Configure Amplify
const amplifyConfig = {
  Auth: {
    Cognito: {
      userPoolId: 'us-west-2_KvNDBMljE',
      userPoolClientId: '6sc0nqta7a2kt727shji0qqeen',
      identityPoolId: 'us-west-2:c839acd7-81ed-4266-8776-89068288760c',
      loginWith: {
        email: true,
      },
      signUpVerificationMethod: 'code' as const,
      userAttributes: {
        email: {
          required: true,
        },
      },
      allowGuestAccess: true,
      passwordFormat: {
        minLength: 8,
        requireLowercase: true,
        requireUppercase: true,
        requireNumbers: true,
        requireSpecialCharacters: true,
      },
    },
  },
}

Amplify.configure(amplifyConfig)

export default function App({ Component, pageProps }: AppProps) {
  return <Component {...pageProps} />
}
