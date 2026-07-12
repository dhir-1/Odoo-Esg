import { useState } from "react";
import { Link, useLocation } from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";
import {
  Bell,
  FileText,
  Leaf,
  LayoutDashboard,
  Menu,
  Search,
  Settings,
  Shield,
  Trophy,
  Users,
  LogOut,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { useAuth } from "@/contexts/auth-context";


interface NavSection {
  name: string;
  to: "/" | "/environmental" | "/social" | "/governance" | "/gamification" | "/reports" | "/settings";
  icon: React.ComponentType<{ className?: string }>;
  color: "primary" | "secondary" | "accent" | "gold";
  items: string[];
}

const navSections: NavSection[] = [
  {
    name: "Dashboard",
    to: "/",
    icon: LayoutDashboard,
    color: "primary",
    items: [],
  },
  {
    name: "Environmental",
    to: "/environmental",
    icon: Leaf,
    color: "accent",
    items: [
      "Emission Factors",
      "Product ESG Profiles",
      "Carbon Transactions",
      "Environmental Goals",
    ],
  },
  {
    name: "Social",
    to: "/social",
    icon: Users,
    color: "secondary",
    items: ["CSR Activities", "Employee Participation", "Diversity Dashboard"],
  },
  {
    name: "Governance",
    to: "/governance",
    icon: Shield,
    color: "primary",
    items: [
      "Policies",
      "Policy Acknowledgements",
      "Audits",
      "Compliance Issues",
    ],
  },
  {
    name: "Gamification",
    to: "/gamification",
    icon: Trophy,
    color: "gold",
    items: [
      "Challenges",
      "Challenge Participation",
      "Badges",
      "Rewards",
      "Leaderboard",
    ],
  },
  {
    name: "Reports",
    to: "/reports",
    icon: FileText,
    color: "primary",
    items: [
      "Environmental Report",
      "Social Report",
      "Governance Report",
      "ESG Summary",
      "Custom Report Builder",
    ],
  },
  {
    name: "Settings",
    to: "/settings",
    icon: Settings,
    color: "primary",
    items: [
      "Departments",
      "Categories",
      "ESG Configuration",
      "Notification Settings",
    ],
  },
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
  onClick,
}: {
  section: NavSection;
  isActive: boolean;
  onClick?: () => void;
}) {
  const Icon = section.icon;
  return (
    <Link
      to={section.to}
      onClick={onClick}
      className={cn(
        "group relative flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors duration-200",
        isActive ? "bg-muted" : "hover:bg-muted",
      )}
    >
      {isActive && (
        <motion.div
          layoutId="nav-indicator"
          className="absolute bottom-2 left-0 top-2 w-1 rounded-r-full bg-primary"
          transition={{ type: "spring", stiffness: 300, damping: 30 }}
        />
      )}
      <Icon className={cn("h-5 w-5 shrink-0", colorText[section.color])} />
      <span className="font-body text-foreground">{section.name}</span>
    </Link>
  );
}

function SidebarContent({ onNavigate }: { onNavigate?: () => void }) {
  const { pathname } = useLocation();
  const { user } = useAuth();

  // Filter settings to Admin-only
  const allowedSections = navSections.filter(
    (section) => section.to !== "/settings" || user?.role === "Admin"
  );

  return (
    <div className="flex h-full flex-col">
      <div className="flex h-16 items-center gap-2 border-b border-border px-6">
        <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary text-primary-foreground">
          <Leaf className="h-5 w-5" />
        </div>
        <span className="font-display text-xl font-semibold text-foreground">
          EcoSphere
        </span>
      </div>

      <nav className="flex-1 overflow-y-auto px-3 py-4">
        <ul className="space-y-6">
          {allowedSections.map((section) => {
            const isActive =
              pathname === section.to ||
              (section.to !== "/" && pathname.startsWith(section.to));
            return (
              <li key={section.name}>
                <NavItem
                  section={section}
                  isActive={isActive}
                  onClick={onNavigate}
                />
                {section.items.length > 0 && (
                  <ul className="ml-3 mt-1 space-y-0.5 border-l border-border pl-7">
                    {section.items.map((item) => (
                      <li key={item}>
                        <span className="block rounded-md px-3 py-1.5 text-sm text-muted-foreground transition-colors hover:text-foreground">
                          {item}
                        </span>
                      </li>
                    ))}
                  </ul>
                )}
              </li>
            );
          })}
        </ul>
      </nav>

      <div className="border-t border-border p-4">
        <div className="rounded-lg bg-muted p-3">
          <p className="font-body text-xs font-medium text-muted-foreground">
            EcoSphere v1.0
          </p>
        </div>
      </div>
    </div>
  );
}

function TopBar({ onMenuClick }: { onMenuClick: () => void }) {
  const { user, logout } = useAuth();
  
  const getInitials = (name?: string) => {
    if (!name) return "ES";
    return name
      .split(" ")
      .map((n) => n[0])
      .join("")
      .slice(0, 2)
      .toUpperCase();
  };

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
        <div className="flex items-center gap-2">
          <div className="flex h-7 w-7 items-center justify-center rounded-md bg-primary text-primary-foreground lg:hidden">
            <Leaf className="h-4 w-4" />
          </div>
          <span className="font-display text-lg font-semibold text-foreground">
            EcoSphere
          </span>
        </div>
      </div>

      <div className="flex flex-1 items-center justify-end gap-4">
        <div className="relative hidden w-full max-w-md sm:block">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <input
            type="search"
            placeholder="Search..."
            className="h-10 w-full rounded-lg border border-border bg-background pl-9 pr-4 font-body text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring"
          />
        </div>

        <button
          type="button"
          className="relative inline-flex h-10 w-10 items-center justify-center rounded-lg transition-colors hover:bg-muted"
          aria-label="Notifications"
        >
          <Bell className="h-5 w-5 text-foreground" />
          <span className="absolute right-2 top-2 h-2 w-2 rounded-full bg-danger" />
        </button>

        <div className="flex items-center gap-3 border-r border-border pr-4">
          <div className="flex h-9 w-9 items-center justify-center rounded-full bg-primary font-body text-sm font-medium text-primary-foreground">
            {getInitials(user?.full_name)}
          </div>
          <div className="hidden leading-none md:block">
            <p className="font-body text-sm font-medium text-foreground">
              {user?.full_name || "Guest User"}
            </p>
            <p className="font-body text-xs text-muted-foreground">
              {user?.designation || user?.role || "Visitor"}
            </p>
          </div>
        </div>

        <button
          type="button"
          onClick={logout}
          className="inline-flex h-10 w-10 items-center justify-center rounded-lg text-muted-foreground transition-colors hover:bg-muted hover:text-danger"
          title="Log Out"
        >
          <LogOut className="h-5 w-5" />
        </button>
      </div>
    </header>
  );
}

export function AppLayout({ children }: { children: React.ReactNode }) {
  const [mobileOpen, setMobileOpen] = useState(false);

  return (
    <div className="flex h-screen w-full overflow-hidden bg-background font-sans text-foreground">
      <aside className="hidden w-64 shrink-0 flex-col border-r border-border bg-card lg:flex">
        <SidebarContent />
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
        <TopBar onMenuClick={() => setMobileOpen(true)} />
        <main className="flex-1 overflow-y-auto p-4 lg:p-8">{children}</main>
      </div>
    </div>
  );
}
