import { Navigate, Route, Routes } from 'react-router-dom'
import Layout from './components/Layout'
import ProtectedRoute from './components/ProtectedRoute'
import Analytics from './pages/Analytics'
import Dashboard from './pages/Dashboard'
import Emails from './pages/Emails'
import EmailThreadDetail from './pages/EmailThreadDetail'
import ImportPage from './pages/Import'
import Login from './pages/Login'
import PlaceholderPage from './pages/Placeholder'
import ProcessingPage from './pages/Processing'
import Register from './pages/Register'
import StakeholderComparison from './pages/StakeholderComparison'
import StakeholderNetwork from './pages/StakeholderNetwork'
import StakeholderProfile from './pages/StakeholderProfile'
import Stakeholders from './pages/Stakeholders'
import { ROUTES } from './utils/constants'

function ProtectedLayout({ children }) {
  return (
    <ProtectedRoute>
      <Layout>{children}</Layout>
    </ProtectedRoute>
  )
}

export default function App() {
  return (
    <Routes>
      <Route path={ROUTES.LOGIN} element={<Login />} />
      <Route path={ROUTES.REGISTER} element={<Register />} />
      <Route path={ROUTES.DASHBOARD} element={<ProtectedLayout><Dashboard /></ProtectedLayout>} />
      <Route path={ROUTES.IMPORT} element={<ProtectedLayout><ImportPage /></ProtectedLayout>} />
      <Route path={ROUTES.PROCESSING} element={<ProtectedLayout><ProcessingPage /></ProtectedLayout>} />
      <Route path={ROUTES.CONTRACTS} element={<ProtectedLayout><PlaceholderPage title="Contracts" /></ProtectedLayout>} />
      <Route path={ROUTES.STAKEHOLDER_COMPARISON} element={<ProtectedLayout><StakeholderComparison /></ProtectedLayout>} />
      <Route path={ROUTES.STAKEHOLDER_NETWORK} element={<ProtectedLayout><StakeholderNetwork /></ProtectedLayout>} />
      <Route path={ROUTES.STAKEHOLDER_PROFILE} element={<ProtectedLayout><StakeholderProfile /></ProtectedLayout>} />
      <Route path={ROUTES.STAKEHOLDERS} element={<ProtectedLayout><Stakeholders /></ProtectedLayout>} />
      <Route path={ROUTES.EMAIL_THREAD_DETAIL} element={<ProtectedLayout><EmailThreadDetail /></ProtectedLayout>} />
      <Route path={ROUTES.EMAIL_CLASSIFICATION} element={<ProtectedLayout><Emails /></ProtectedLayout>} />
      <Route path={ROUTES.EMAILS} element={<ProtectedLayout><Emails /></ProtectedLayout>} />
      <Route path={ROUTES.ANALYTICS} element={<ProtectedLayout><Analytics /></ProtectedLayout>} />
      <Route path="*" element={<Navigate to={ROUTES.DASHBOARD} replace />} />
    </Routes>
  )
}
