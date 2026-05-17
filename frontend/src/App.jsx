import { Navigate, Route, Routes } from 'react-router-dom'
import Layout from './components/Layout'
import ProtectedRoute from './components/ProtectedRoute'
import Dashboard from './pages/Dashboard'
import ImportPage from './pages/Import'
import Login from './pages/Login'
import PlaceholderPage from './pages/Placeholder'
import ProcessingPage from './pages/Processing'
import Register from './pages/Register'
import { ROUTES } from './utils/constants'

export default function App() {
  return (
    <Routes>
      <Route path={ROUTES.LOGIN} element={<Login />} />
      <Route path={ROUTES.REGISTER} element={<Register />} />
      <Route
        path={ROUTES.DASHBOARD}
        element={
          <ProtectedRoute>
            <Layout>
              <Dashboard />
            </Layout>
          </ProtectedRoute>
        }
      />
      <Route
        path={ROUTES.IMPORT}
        element={
          <ProtectedRoute>
            <Layout>
              <ImportPage />
            </Layout>
          </ProtectedRoute>
        }
      />
      <Route
        path={ROUTES.PROCESSING}
        element={
          <ProtectedRoute>
            <Layout>
              <ProcessingPage />
            </Layout>
          </ProtectedRoute>
        }
      />
      <Route
        path={ROUTES.CONTRACTS}
        element={
          <ProtectedRoute>
            <Layout>
              <PlaceholderPage title="Contracts" />
            </Layout>
          </ProtectedRoute>
        }
      />
      <Route
        path={ROUTES.STAKEHOLDERS}
        element={
          <ProtectedRoute>
            <Layout>
              <PlaceholderPage title="Stakeholders" />
            </Layout>
          </ProtectedRoute>
        }
      />
      <Route
        path={ROUTES.EMAILS}
        element={
          <ProtectedRoute>
            <Layout>
              <PlaceholderPage title="Emails" />
            </Layout>
          </ProtectedRoute>
        }
      />
      <Route
        path={ROUTES.ANALYTICS}
        element={
          <ProtectedRoute>
            <Layout>
              <PlaceholderPage title="Analytics" />
            </Layout>
          </ProtectedRoute>
        }
      />
      <Route path="*" element={<Navigate to={ROUTES.DASHBOARD} replace />} />
    </Routes>
  )
}
