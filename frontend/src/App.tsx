import React, { useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Link, Navigate } from 'react-router-dom';
import { Provider, useSelector, useDispatch } from 'react-redux';
import { store, RootState } from './redux/store';
import { ResumeUpload } from './pages/ResumeUpload';
import { JDAnalysis } from './pages/JDAnalysis';
import { Dashboard } from './pages/Dashboard';
import { MatchResults } from './pages/MatchResults';
import { Login } from './pages/Login';
import { Signup } from './pages/Signup';
import { restoreSession } from './hooks/useAppInit';
import { logout } from './redux/slices/authSlice';

const ProtectedRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { isAuthenticated } = useSelector((state: RootState) => state.auth);
  return isAuthenticated ? <>{children}</> : <Navigate to="/login" />;
};

const PublicRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { isAuthenticated } = useSelector((state: RootState) => state.auth);
  return isAuthenticated ? <Navigate to="/" /> : <>{children}</>;
};

const AppContent: React.FC = () => {
  const { isAuthenticated, user } = useSelector((state: RootState) => state.auth);
  const dispatch = useDispatch();

  useEffect(() => {
    if (isAuthenticated && !user) {
      restoreSession(dispatch);
    }
  }, [dispatch, isAuthenticated, user]);

  return (
    <Router>
      <div className="min-h-screen bg-gray-50">
        <nav className="bg-white shadow">
          <div className="max-w-7xl mx-auto px-6 py-4 flex justify-between items-center">
            <Link to="/" className="text-2xl font-bold text-blue-600">
              HireScope
            </Link>
            
            <div className="flex space-x-6 items-center">
              {isAuthenticated ? (
                <>
                  <Link to="/upload" className="text-gray-600 hover:text-blue-600">
                    Upload Resume
                  </Link>
                  <Link to="/analyze-jd" className="text-gray-600 hover:text-blue-600">
                    Analyze JD
                  </Link>
                  <span className="text-gray-600">{user?.email}</span>
                  <button
                    onClick={() => {
                      dispatch(logout());
                      window.location.href = '/login';
                    }}
                    className="text-red-600 hover:text-red-800"
                  >
                    Logout
                  </button>
                </>
              ) : (
                <>
                  <Link to="/login" className="text-gray-600 hover:text-blue-600">
                    Login
                  </Link>
                  <Link to="/signup" className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700">
                    Sign Up
                  </Link>
                </>
              )}
            </div>
          </div>
        </nav>

        <main>
          <Routes>
            <Route path="/" element={<ProtectedRoute><Dashboard /></ProtectedRoute>} />
            <Route path="/upload" element={<ProtectedRoute><ResumeUpload /></ProtectedRoute>} />
            <Route path="/analyze-jd" element={<ProtectedRoute><JDAnalysis /></ProtectedRoute>} />
            <Route path="/login" element={<PublicRoute><Login /></PublicRoute>} />
            <Route path="/signup" element={<PublicRoute><Signup /></PublicRoute>} />
            <Route path="/results/:resumeId/:jdId" element={<ProtectedRoute><MatchResults /></ProtectedRoute>} />
          </Routes>
        </main>
      </div>
    </Router>
  );
};

function App() {
  return (
    <Provider store={store}>
      <AppContent />
    </Provider>
  );
}

export default App;
