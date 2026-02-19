import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { AuthProvider } from './contexts/AuthContext';
import ProtectedRoute from './components/ProtectedRoute';
import ErrorBoundary from './components/ErrorBoundary';
import LoginPage from './pages/LoginPage';
import HomePage from './pages/HomePage';
import VideosPage from './pages/VideosPage';
import VideoDetailPage from './pages/VideoDetailPage';
import ClipsPage from './pages/ClipsPage';
import HighlightsPage from './pages/HighlightsPage';
import SharePage from './pages/SharePage';
import UsersPage from './pages/UsersPage';

function App() {
  return (
    <ErrorBoundary>
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/share/:token" element={<SharePage />} />

          <Route path="/" element={<ProtectedRoute><HomePage /></ProtectedRoute>} />
          <Route path="/videos" element={<ProtectedRoute><VideosPage /></ProtectedRoute>} />
          <Route path="/videos/:id" element={<ProtectedRoute><VideoDetailPage /></ProtectedRoute>} />
          <Route path="/clips" element={<ProtectedRoute><ClipsPage /></ProtectedRoute>} />
          <Route path="/highlights" element={<ProtectedRoute><HighlightsPage /></ProtectedRoute>} />
          <Route path="/users" element={<ProtectedRoute requireAdmin><UsersPage /></ProtectedRoute>} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
    </ErrorBoundary>
  );
}

export default App;
