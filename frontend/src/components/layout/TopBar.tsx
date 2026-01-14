import { useNavigate } from 'react-router-dom'
import { useAuth } from '../../app/store/authContext'
import { NotificationDropdown } from './NotificationDropdown'
import { Button } from '../ui/Button'

interface TopBarProps {
  onMenuClick: () => void
}

export function TopBar({ onMenuClick }: TopBarProps) {
  const navigate = useNavigate()
  const { logout } = useAuth()

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  return (
    <header className="bg-white border-b border-gray-200 px-6 py-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <button
            onClick={onMenuClick}
            className="lg:hidden text-gray-600 hover:text-gray-900"
          >
            <span className="text-2xl">☰</span>
          </button>
          <h2 className="text-lg font-semibold text-gray-900">SMD System</h2>
        </div>
        <div className="flex items-center space-x-4">
          <NotificationDropdown />
          <Button variant="outline" size="sm" onClick={handleLogout}>
            Logout
          </Button>
        </div>
      </div>
    </header>
  )
}
