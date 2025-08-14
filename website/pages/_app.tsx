import type { AppProps } from 'next/app'
import '../styles/globals.css'
import '@aws-amplify/ui-react/styles.css'
import '../lib/amplify-config'

export default function App({ Component, pageProps }: AppProps) {
  return <Component {...pageProps} />
}
