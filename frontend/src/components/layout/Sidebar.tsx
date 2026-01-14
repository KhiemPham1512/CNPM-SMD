import { NavLink } from 'react-router-dom'
import { useAuth } from '../../app/store/authContext'
import { UserRole } from '../../types'

interface SidebarProps {
  open: boolean
  onToggle: () => void
}

interface MenuItem {
  label: string
  path: string
  icon: string
  roles: UserRole[]
}

const menuItems: MenuItem[] = [
  {
    label: 'Dashboard',
    path: '/app/dashboard',
    icon: '📊',
    roles: ['ADMIN', 'LECTURER', 'HOD', 'AA', 'PRINCIPAL', 'STUDENT'],
  },
  {
    label: 'Syllabi',
    path: '/app/syllabi',
    icon: '📚',
    roles: ['ADMIN', 'LECTURER', 'HOD', 'AA', 'PRINCIPAL', 'STUDENT'],
  },
  {
    label: 'Notifications',
    path: '/app/notifications',
    icon: '🔔',
    roles: ['ADMIN', 'LECTURER', 'HOD', 'AA', 'PRINCIPAL', 'STUDENT'],
  },
  {
    label: 'User Management',
    path: '/app/admin/users',
    icon: '👥',
    roles: ['ADMIN'],
  },
  {
    label: 'Public Search',
    path: '/public/search',
    icon: '🔍',
    roles: ['STUDENT'],
  },
]

export function Sidebar({ open, onToggle }: SidebarProps) {
  const { state } = useAuth()
  const userRole = state.roles[0] as UserRole | undefined

  const filteredItems = menuItems.filter(item => 
    userRole && item.roles.includes(userRole)
  )

  return (
    <>
      {open && (
        <div className="fixed inset-0 bg-black bg-opacity-50 z-20 lg:hidden" onClick={onToggle} />
      )}
      <aside
        className={`
          fixed lg:static inset-y-0 left-0 z-30
          w-64 bg-white border-r border-gray-200
          transform transition-transform duration-300 ease-in-out
          ${open ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'}
        `}
      >
        <div className="flex flex-col h-full">
          <div className="p-4 border-b border-gray-200">
            <h1 className="text-xl font-bold text-gray-900">SMD</h1>
            <p className="text-sm text-gray-600">Syllabus Management</p>
          </div>
          <nav className="flex-1 p-4 space-y-2">
            {filteredItems.map(item => (
              <NavLink
                key={item.path}
                to={item.path}
                className={({ isActive }) =>
                  `flex items-center space-x-3 px-4 py-3 rounded-lg transition-colors ${
                    isActive
                      ? 'bg-primary-50 text-primary-700 border border-primary-200'
                      : 'text-gray-700 hover:bg-gray-100'
                  }`
                }
              >
                <span className="text-xl">{item.icon}</span>
                <span>{item.label}</span>
              </NavLink>
            ))}
          </nav>
          <div className="p-4 border-t border-gray-200">
            <div className="text-sm text-gray-600">
              <div className="font-medium text-gray-900">{state.user?.full_name}</div>
              <div className="text-xs mt-1">{userRole}</div>
            </div>
          </div>
        </div>
      </aside>
    </>
  )
}
