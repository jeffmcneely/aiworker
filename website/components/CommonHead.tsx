import Head from 'next/head'

interface CommonHeadProps {
  title?: string
  description?: string
}

export default function CommonHead({ 
  title = 'AI Image Generator', 
  description = 'Generate AI images with flux, hidream, and omnigen models'
}: CommonHeadProps) {
  return (
    <Head>
      <meta charSet="UTF-8" />
      <meta name="viewport" content="width=device-width, initial-scale=1.0" />
      <link rel="preconnect" href="https://fonts.googleapis.com" />
      <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
      <link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&display=swap" rel="stylesheet" />
      <link rel="apple-touch-icon" sizes="180x180" href="/calico-180x180.png" />
      <link rel="icon" type="image/png" sizes="32x32" href="/calico-32x32.png" />
      <link rel="icon" type="image/png" sizes="16x16" href="/calico-16x16.png" />
      <link rel="manifest" href="/site.webmanifest" />
      <meta name="msapplication-config" content="/browserconfig.xml" />
      <meta name="theme-color" content="#ffffff" />
      <meta name="description" content={description} />
      <title>{title}</title>
    </Head>
  )
}
