import { createBrowserRouter, Navigate } from 'react-router-dom'
import { ProtectedRoute } from './components/ProtectedRoute'
import { AdminGuard, LecturerGuard, HodGuard, AAGuard, PrincipalGuard } from './components/RoleGuard'
import { LoginPage } from '../features/auth/LoginPage'
import { RegisterPage } from '../features/auth/RegisterPage'
import { DashboardPage } from '../features/dashboard/DashboardPage'
import { SyllabusListPage } from '../features/syllabi/SyllabusListPage'
import { SyllabusDetailPage } from '../features/syllabi/SyllabusDetailPage'
import { SyllabusComparePage } from '../features/syllabi/SyllabusComparePage'
import { SyllabusCreatePage } from '../features/syllabi/SyllabusCreatePage'
import { SyllabusEditPage } from '../features/syllabi/SyllabusEditPage'
import { NotificationCenterPage } from '../features/notifications/NotificationCenterPage'
import { UserManagementPage } from '../features/users/UserManagementPage'
import { PublicSearchPage } from '../features/student/PublicSearchPage'
import { PublicSyllabusPage } from '../features/student/PublicSyllabusPage'
import { HodReviewQueuePage } from '../features/hod/HodReviewQueuePage'
import { HodReviewDetailPage } from '../features/hod/HodReviewDetailPage'
import { AaReviewQueuePage } from '../features/aa/AaReviewQueuePage'
import { AaReviewDetailPage } from '../features/aa/AaReviewDetailPage'
import { PrincipalReviewQueuePage } from '../features/principal/PrincipalReviewQueuePage'
import { PrincipalReviewDetailPage } from '../features/principal/PrincipalReviewDetailPage'
import { SystemSettingsPage } from '../features/admin/SystemSettingsPage'
import { PublishingManagementPage } from '../features/admin/PublishingManagementPage'

export const router = createBrowserRouter([
  {
    path: '/login',
    element: <LoginPage />,
  },
  {
    path: '/register',
    element: <RegisterPage />,
  },
  {
    path: '/app',
    element: <ProtectedRoute />,
    children: [
      {
        index: true,
        element: <Navigate to="/app/dashboard" replace />,
      },
      {
        path: 'dashboard',
        element: <DashboardPage />,
      },
      {
        path: 'syllabi',
        element: <SyllabusListPage />,
      },
      {
        path: 'syllabi/new',
        element: (
          <LecturerGuard>
            <SyllabusCreatePage />
          </LecturerGuard>
        ),
      },
      {
        path: 'syllabi/:id',
        element: <SyllabusDetailPage />,
      },
      {
        path: 'syllabi/:id/edit',
        element: (
          <LecturerGuard>
            <SyllabusEditPage />
          </LecturerGuard>
        ),
      },
      {
        path: 'syllabi/:id/compare',
        element: <SyllabusComparePage />,
      },
      {
        path: 'notifications',
        element: <NotificationCenterPage />,
      },
      {
        path: 'admin/users',
        element: (
          <AdminGuard>
            <UserManagementPage />
          </AdminGuard>
        ),
      },
      {
        path: 'hod/reviews',
        element: (
          <HodGuard>
            <HodReviewQueuePage />
          </HodGuard>
        ),
      },
      {
        path: 'hod/reviews/:syllabusId',
        element: (
          <HodGuard>
            <HodReviewDetailPage />
          </HodGuard>
        ),
      },
      {
        path: 'aa/reviews',
        element: (
          <AAGuard>
            <AaReviewQueuePage />
          </AAGuard>
        ),
      },
      {
        path: 'aa/reviews/:syllabusId',
        element: (
          <AAGuard>
            <AaReviewDetailPage />
          </AAGuard>
        ),
      },
      {
        path: 'principal/reviews',
        element: (
          <PrincipalGuard>
            <PrincipalReviewQueuePage />
          </PrincipalGuard>
        ),
      },
      {
        path: 'principal/reviews/:syllabusId',
        element: (
          <PrincipalGuard>
            <PrincipalReviewDetailPage />
          </PrincipalGuard>
        ),
      },
      {
        path: 'admin/system-settings',
        element: (
          <AdminGuard>
            <SystemSettingsPage />
          </AdminGuard>
        ),
      },
      {
        path: 'admin/publishing',
        element: (
          <AdminGuard>
            <PublishingManagementPage />
          </AdminGuard>
        ),
      },
    ],
  },
  {
    path: '/public',
    children: [
      {
        path: 'search',
        element: <PublicSearchPage />,
      },
      {
        path: 'syllabi/:id',
        element: <PublicSyllabusPage />,
      },
    ],
  },
  {
    path: '/',
    element: <Navigate to="/login" replace />,
  },
  {
    path: '*',
    element: <Navigate to="/login" replace />,
  },
])
