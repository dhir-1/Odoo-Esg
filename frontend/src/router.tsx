import { createBrowserRouter, Navigate } from "react-router-dom";
import { AppLayout } from "./components/ecosphere/app-layout";
import { DashboardPage } from "./routes/index";
import { EnvironmentalPage } from "./routes/environmental";
import { SocialPage } from "./routes/social";
import { GovernancePage } from "./routes/governance";
import { GamificationPage } from "./routes/gamification";
import { ReportsPage } from "./routes/reports";
import { SettingsPage } from "./routes/settings";
import { LoginPage } from "./routes/login";
import { useAuth } from "./contexts/auth-context";

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { token, user, loading } = useAuth();

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-background">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
      </div>
    );
  }

  if (!token || !user) {
    return <Navigate to="/login" replace />;
  }

  return <>{children}</>;
}

function withAppLayout(element: React.ReactElement) {
  return (
    <ProtectedRoute>
      <AppLayout>{element}</AppLayout>
    </ProtectedRoute>
  );
}

const NotFoundPage = () => (
  <div className="flex min-h-screen items-center justify-center bg-background px-4">
    <div className="max-w-md text-center">
      <h1 className="text-7xl font-bold text-foreground">404</h1>
      <h2 className="mt-4 text-xl font-semibold text-foreground">Page not found</h2>
      <p className="mt-2 text-sm text-muted-foreground">
        The page you are looking for does not exist or has been moved.
      </p>
      <div className="mt-6">
        <a
          href="/"
          className="inline-flex items-center justify-center rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground transition-colors hover:bg-primary/90"
        >
          Go home
        </a>
      </div>
    </div>
  </div>
);

export const router = createBrowserRouter([
  {
    path: "/login",
    element: <LoginPage />,
  },
  {
    path: "/",
    element: withAppLayout(<DashboardPage />),
  },
  {
    path: "/environmental",
    element: withAppLayout(<EnvironmentalPage />),
  },
  {
    path: "/social",
    element: withAppLayout(<SocialPage />),
  },
  {
    path: "/governance",
    element: withAppLayout(<GovernancePage />),
  },
  {
    path: "/gamification",
    element: withAppLayout(<GamificationPage />),
  },
  {
    path: "/reports",
    element: withAppLayout(<ReportsPage />),
  },
  {
    path: "/settings",
    element: withAppLayout(<SettingsPage />),
  },
  {
    path: "*",
    element: withAppLayout(<NotFoundPage />),
  },
]);
