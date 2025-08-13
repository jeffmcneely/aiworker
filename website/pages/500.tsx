import Image from 'next/image'

export default function Custom500() {
  return (
    <div style={{ textAlign: 'center', marginTop: '40px' }}>
      <Image src="/500.png" alt="500 - Server Error" width={300} height={300} />
      <h1 style={{ marginTop: '24px' }}>there&apos;s a problem on my end</h1>
    </div>
  )
}
