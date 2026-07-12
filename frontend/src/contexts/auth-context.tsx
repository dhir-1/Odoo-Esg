import { createContext, useContext, useState, useEffect, ReactNode } from "react";
import { apiFetch } from "@/lib/api-client";

export interface Employee {
  id: int;
  employee_code: string;
  full_name: string;
  email: string;
  role: "Admin" | "Manager" | "Employee";
  department_id: number;
  designation: string;
  date_joined: string;
  xp_points: number;
  points_balance: number;
  status: "Active" | "Inactive";
  avatar_url?: string;
  created_at: string;
  updated_at: string;
}

interface AuthContextType {
  user: Employee | null;
  token: string | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<Employee>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<Employee | null>(null);
  const [token, setToken] = useState<string | null>(sessionStorage.getItem("token"));
  const [loading, setLoading] = useState(true);

  const rehydrate = async (savedToken: string) => {
    try {
      const userData = await apiFetch<Employee>("/auth/me");
      setUser(userData);
    } catch {
      logout();
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    const savedToken = sessionStorage.getItem("token");
    if (savedToken) {
      setToken(savedToken);
      rehydrate(savedToken);
    } else {
      setLoading(false);
    }
  }, []);

  const login = async (email: string, password: string): Promise<Employee> => {
    const res = await apiFetch<{ access_token: string }>("/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    });

    sessionStorage.setItem("token", res.access_token);
    setToken(res.access_token);
    
    const userData = await apiFetch<Employee>("/auth/me");
    setUser(userData);
    return userData;
  };

  const logout = () => {
    sessionStorage.removeItem("token");
    setToken(null);
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, token, loading, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
