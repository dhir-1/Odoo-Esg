import { useEffect, useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";
import {
  Bell,
  FileText,
  Leaf,
  LayoutDashboard,
  Menu,
  PanelLeftClose,
  PanelLeftOpen,
  RefreshCw,
  Search,
  Settings,
  Shield,
  Trophy,
  Users,
  LogOut,
  UserCircle2,
  MailOpen,
  Clock3,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { useAuth } from "@/contexts/auth-context";
import { apiFetch } from "@/lib/api-client";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { sampleNotifications } from "@/lib/dashboard-mock-data";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { ScrollArea } from "@/components/ui/scroll-area";

interface NavSection {
  name: string;
  to: "/" | "/environmental" | "/social" | "/governance" | "/gamification" | "/reports" | "/settings";
  icon: React.ComponentType<{ className?: string }>;
  color: "primary" | "secondary" | "accent" | "gold";
}

const navSections: NavSection[] = [
  { name: "Dashboard", to: "/", icon: LayoutDashboard, color: "primary" },
  { name: "Environmental", to: "/environmental", icon: Leaf, color: "accent" },
  { name: "Social", to: "/social", icon: Users, color: "secondary" },
  { name: "Governance", to: "/governance", icon: Shield, color: "primary" },
  { name: "Gamification", to: "/gamification", icon: Trophy, color: "gold" },
  { name: "Reports", to: "/reports", icon: FileText, color: "primary" },
  { name: "Settings", to: "/settings", icon: Settings, color: "primary" },
];

const colorText = {
  primary: "text-primary",
  secondary: "text-secondary",
  accent: "text-accent",
  gold: "text-gold",
};

function NavItem({
  section,
  isActive,
  collapsed = false,
  onClick,
}: {
  section: NavSection;
  isActive: boolean;
  collapsed?: boolean;
  onClick?: () => void;
}) {
  const Icon = section.icon;
  return (
    <Link
      to={section.to}
      onClick={onClick}
      className={cn(
        "group relative flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors duration-200",
        collapsed && "justify-center px-2",
        isActive ? "bg-muted" : "hover:bg-muted",
      )}
      title={collapsed ? section.name : undefined}
    >
      {isActive && (
        <motion.div
          layoutId="nav-indicator"
          className="absolute bottom-2 left-0 top-2 w-1 rounded-r-full bg-primary"
          transition={{ type: "spring", stiffness: 300, damping: 30 }}
        />
      )}
      <Icon className={cn("h-5 w-5 shrink-0", colorText[section.color])} />
      {!collapsed && <span className="font-body text-foreground">{section.name}</span>}
    </Link>
  );
}

function SidebarContent({
  collapsed = false,
  onNavigate,
}: {
  collapsed?: boolean;
  onNavigate?: () => void;
}) {
  const { pathname } = useLocation();
  const { user } = useAuth();

  const allowedSections = navSections.filter(
    (section) =>
      (section.to !== "/settings" || user?.role === "Admin") &&
      (section.to !== "/governance" || user?.role === "Admin" || user?.role === "Manager"),
  );

  return (
    <div className="flex h-full flex-col">
      <div
        className={cn(
          "flex h-16 items-center border-b border-border",
          collapsed ? "justify-center px-3" : "gap-2 px-6",
        )}
      >
        <img src="/brand-logo.svg" alt="" className="h-8 w-8" />
        {!collapsed && (
          <span className="font-display text-xl font-semibold text-foreground">
            Soteria
          </span>
        )}
      </div>

      <nav className="flex-1 overflow-y-auto px-3 py-4">
        <ul className="space-y-3">
          {allowedSections.map((section) => {
            const isActive =
              pathname === section.to ||
              (section.to !== "/" && pathname.startsWith(section.to));
            return (
              <li key={section.name}>
                <NavItem
                  section={section}
                  isActive={isActive}
                  collapsed={collapsed}
                  onClick={onNavigate}
                />
              </li>
            );
          })}
        </ul>
      </nav>
    </div>
  );
}

interface NotificationItem {
  id: number;
  title: string;
  message: string;
  is_read: boolean;
  created_at: string;
  type: string;
}

function TopBar({
  onMenuClick,
  onToggleSidebar,
  isSidebarCollapsed,
}: {
  onMenuClick: () => void;
  onToggleSidebar: () => void;
  isSidebarCollapsed: boolean;
}) {
  const { user, token, logout } = useAuth();
  const navigate = useNavigate();
  const [notifications, setNotifications] = useState<NotificationItem[]>([]);
  const [notificationsLoading, setNotificationsLoading] = useState(false);
  const [logoutOpen, setLogoutOpen] = useState(false);

  const getInitials = (name?: string) => {
    if (!name) return "ES";
    return name
      .split(" ")
      .map((n) => n[0])
      .join("")
      .slice(0, 2)
      .toUpperCase();
  };

  const loadNotifications = async () => {
    if (!token) return;
    setNotificationsLoading(true);
    try {
      const items = await apiFetch<NotificationItem[]>("/notifications?limit=6&is_read=false");
      setNotifications(items);
    } catch {
      setNotifications([]);
    } finally {
      setNotificationsLoading(false);
    }
  };

  useEffect(() => {
    loadNotifications();
  }, [token]);

  const visibleNotifications = notifications.length > 0 ? notifications : sampleNotifications;
  const unreadCount = visibleNotifications.filter((item) => !item.is_read).length;
  const initials = getInitials(user?.full_name);

  return (
    <header className="flex h-16 shrink-0 items-center justify-between gap-4 border-b border-border bg-card px-4 lg:px-8">
      <div className="flex items-center gap-3">
        <button
          type="button"
          onClick={onMenuClick}
          className="inline-flex h-10 w-10 items-center justify-center rounded-lg transition-colors hover:bg-muted lg:hidden"
          aria-label="Open menu"
        >
          <Menu className="h-5 w-5 text-foreground" />
        </button>
        <button
          type="button"
          onClick={onToggleSidebar}
          className="hidden h-10 items-center gap-2 rounded-lg px-3 text-sm font-medium text-foreground transition-colors hover:bg-muted lg:inline-flex"
          aria-label={isSidebarCollapsed ? "Expand sidebar" : "Collapse sidebar"}
        >
          {isSidebarCollapsed ? (
            <PanelLeftOpen className="h-4 w-4" />
          ) : (
            <PanelLeftClose className="h-4 w-4" />
          )}
          <span>{isSidebarCollapsed ? "Expand" : "Collapse"}</span>
        </button>
        <div className="flex items-center gap-2 lg:hidden">
        <img src="/brand-logo.svg" alt="" className="h-8 w-8" />
          <span className="font-display text-lg font-semibold text-foreground">
            Soteria
          </span>
        </div>
      </div>

      <div className="flex min-w-0 flex-1 items-center justify-end gap-2 sm:gap-4">
        <div className="relative hidden w-full max-w-md sm:block">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <input
            type="search"
            placeholder="Search..."
            className="h-10 w-full rounded-lg border border-border bg-background pl-9 pr-4 font-body text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring"
          />
        </div>

        <DropdownMenu onOpenChange={(open) => open && loadNotifications()}>
          <DropdownMenuTrigger asChild>
            <button
              type="button"
              className="relative inline-flex h-10 w-10 items-center justify-center rounded-lg transition-colors hover:bg-muted"
              aria-label="Notifications"
            >
              <Bell className="h-5 w-5 text-foreground" />
              {unreadCount > 0 && (
                <span className="absolute right-2 top-2 h-2 w-2 rounded-full bg-danger" />
              )}
            </button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-[22rem] p-0">
            <div className="flex items-center justify-between border-b border-border px-4 py-3">
              <div>
                <p className="text-sm font-semibold text-foreground">Notifications</p>
                <p className="text-xs text-muted-foreground">{unreadCount} unread</p>
              </div>
              <button
                type="button"
                onClick={loadNotifications}
                className="inline-flex items-center gap-1 rounded-md px-2 py-1 text-xs text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
              >
                <RefreshCw className="h-3.5 w-3.5" />
                Refresh
              </button>
            </div>
            <ScrollArea className="max-h-[20rem]">
              {notificationsLoading ? (
                <div className="px-4 py-6 text-sm text-muted-foreground">
                  Loading notifications...
                </div>
              ) : (
                visibleNotifications.map((notification) => (
                  <button
                    key={notification.id}
                    type="button"
                    className="flex w-full flex-col gap-1 border-b border-border/60 px-4 py-3 text-left transition-colors hover:bg-muted/60 last:border-b-0"
                    onClick={async () => {
                      try {
                        await apiFetch(`/notifications/${notification.id}/read`, { method: "PATCH" });
                        await loadNotifications();
                      } catch {
                        setNotifications((prev) => prev.filter((item) => item.id !== notification.id));
                      }
                    }}
                  >
                    <div className="flex items-center gap-2">
                      <MailOpen className="h-4 w-4 text-primary" />
                      <p className="text-sm font-medium text-foreground">{notification.title}</p>
                    </div>
                    <p className="text-xs text-muted-foreground">{notification.message}</p>
                    <div className="flex items-center gap-2 text-[11px] text-muted-foreground">
                      <Clock3 className="h-3 w-3" />
                      {new Date(notification.created_at).toLocaleString()}
                    </div>
                  </button>
                ))
              )}
            </ScrollArea>
          </DropdownMenuContent>
        </DropdownMenu>

        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <button
              type="button"
              className="flex items-center gap-3 rounded-xl border border-border/0 px-2 py-1.5 transition-colors hover:bg-muted focus:outline-none focus:ring-2 focus:ring-ring"
              aria-label="Open profile menu"
            >
              <Avatar className="h-10 w-10 ring-2 ring-border/50">
                <AvatarImage src={user?.avatar_url} alt={user?.full_name || "User"} />
                <AvatarFallback className="bg-primary text-primary-foreground">
                  {initials}
                </AvatarFallback>
              </Avatar>
              <div className="hidden min-w-0 text-left leading-tight md:block">
                <p className="truncate font-body text-sm font-medium text-foreground">
                  {user?.full_name || "Guest User"}
                </p>
                <p className="truncate font-body text-xs text-muted-foreground">
                  {user?.designation || user?.role || "Visitor"}
                </p>
              </div>
            </button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-64">
            <DropdownMenuLabel>
              <div className="space-y-0.5">
                <p className="text-sm font-semibold text-foreground">{user?.full_name || "Guest User"}</p>
                <p className="text-xs text-muted-foreground">{user?.email}</p>
              </div>
            </DropdownMenuLabel>
            <DropdownMenuSeparator />
            <DropdownMenuItem
              onSelect={(e) => {
                e.preventDefault();
                navigate("/profile");
              }}
              className="gap-2"
            >
              <UserCircle2 className="h-4 w-4" />
              Profile summary
            </DropdownMenuItem>
            <DropdownMenuItem
              onSelect={(e) => {
                e.preventDefault();
                setLogoutOpen(true);
              }}
              className="gap-2 text-danger focus:text-danger"
            >
              <LogOut className="h-4 w-4" />
              Sign out
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>

      <AlertDialog open={logoutOpen} onOpenChange={setLogoutOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Are you sure you want to log out?</AlertDialogTitle>
            <AlertDialogDescription>
              You will be signed out of Soteria and need to log in again to continue.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={() => {
                logout();
                navigate("/login");
              }}
            >
              Log out
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

    </header>
  );
}

export function AppLayout({ children }: { children: React.ReactNode }) {
  const [mobileOpen, setMobileOpen] = useState(false);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);

  return (
    <div className="flex h-screen w-full overflow-hidden bg-background font-sans text-foreground">
      <aside
        className={cn(
          "hidden shrink-0 flex-col border-r border-border bg-card lg:flex",
          sidebarCollapsed ? "w-20" : "w-64",
        )}
      >
        <SidebarContent collapsed={sidebarCollapsed} />
      </aside>

      <AnimatePresence>
        {mobileOpen && (
          <>
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.2 }}
              className="fixed inset-0 z-40 bg-black/20"
              onClick={() => setMobileOpen(false)}
            />
            <motion.aside
              initial={{ x: "-100%" }}
              animate={{ x: 0 }}
              exit={{ x: "-100%" }}
              transition={{ type: "spring", damping: 25, stiffness: 250 }}
              className="fixed left-0 top-0 z-50 flex h-full w-72 flex-col border-r border-border bg-card shadow-card"
            >
              <SidebarContent onNavigate={() => setMobileOpen(false)} />
            </motion.aside>
          </>
        )}
      </AnimatePresence>

      <div className="flex min-w-0 flex-1 flex-col">
        <TopBar
          onMenuClick={() => setMobileOpen(true)}
          onToggleSidebar={() => setSidebarCollapsed((value) => !value)}
          isSidebarCollapsed={sidebarCollapsed}
        />
        <main className="flex-1 overflow-y-auto p-4 lg:p-8">{children}</main>
      </div>
    </div>
  );
}
