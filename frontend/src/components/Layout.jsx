import Sidebar from './Sidebar'
import TopBar from './TopBar'

export default function Layout({ children }) {
  return (
    <div className="min-h-screen p-6">
      <div className="mx-auto grid max-w-7xl grid-cols-1 gap-4 lg:grid-cols-[256px_1fr]">
        <Sidebar />
        <main>
          <TopBar />
          {children}
        </main>
      </div>
    </div>
  )
}
