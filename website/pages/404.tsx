import Image from 'next/image'

export default function Custom404() {
  return (
    <div style={{ textAlign: 'center', marginTop: '40px' }}>
      <Image src="/404.png" alt="404 - Food Not Found" width={300} height={300} />
      <h1 style={{ marginTop: '24px' }}>food not found</h1>
    </div>
  )
}