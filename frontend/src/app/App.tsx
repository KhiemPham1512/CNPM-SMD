import { RouterProvider } from 'react-router-dom'
import { AuthProvider } from './store/authContext'
import { NotificationProvider } from './store/notificationContext'
import { router } from './router'
import { ErrorBoundary } from '../components/ErrorBoundary'

function App() {
  return (
    <ErrorBoundary>
      <AuthProvider>
        <NotificationProvider>
          <RouterProvider router={router} />
        </NotificationProvider>
      </AuthProvider>
    </ErrorBoundary>
  )
}

export default App
