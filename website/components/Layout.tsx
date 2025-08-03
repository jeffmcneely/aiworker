import { ReactNode } from 'react'
import CommonHead from './CommonHead'

interface LayoutProps {
  children: ReactNode
  title?: string
  description?: string
}

export default function Layout({ children, title, description }: LayoutProps) {
  return (
    <>
      <CommonHead title={title} description={description} />
      <div className="container">
        {children}
      </div>
    </>
  )
}
