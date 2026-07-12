import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "@/contexts/auth-context";
import { Card } from "@/components/ecosphere/card";
import { Button } from "@/components/ecosphere/button";
import { apiFetch } from "@/lib/api-client";
import { toast } from "sonner";
import { Leaf, UserPlus, LogIn } from "lucide-react";

interface DepartmentOption {
  id: number;
  name: string;
  code: string;
  status: string;
}

export function LoginPage() {
  const { login } = useAuth();
  const navigate = useNavigate();

  // Mode toggle
  const [isRegister, setIsRegister] = useState(false);

  // Shared fields
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Register-only fields
  const [fullName, setFullName] = useState("");
  const [departmentId, setDepartmentId] = useState<number | "">("");
  const [designation, setDesignation] = useState("Sustainability Advocate");
  const [departments, setDepartments] = useState<DepartmentOption[]>([]);

  // Fetch departments when register mode activates
  useEffect(() => {
    if (isRegister && departments.length === 0) {
      fetchDepartments();
    }
  }, [isRegister]);

  const fetchDepartments = async () => {
    try {
      // Departments list is public-ish via settings, but we can try
      // without auth — if it 401s, we'll handle it gracefully
      const BASE_URL = (import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api/v1").replace(/\/$/, "");
      const res = await fetch(`${BASE_URL}/departments/public`);
      if (res.ok) {
        const data = await res.json();
        setDepartments(data.filter((d: DepartmentOption) => d.status === "Active"));
      }
    } catch {
      // Silently fail — user can still type a department ID
    }
  };

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email || !password) {
      toast.error("Please enter email and password.");
      return;
    }

    setLoading(true);
    setError(null);
    try {
      await login(email, password);
      toast.success("Successfully logged in!");
      navigate("/");
    } catch (err: any) {
      setError(err.message || "Failed to log in. Please check credentials.");
      toast.error(err.message || "Login failed.");
    } finally {
      setLoading(false);
    }
  };

  const handleSignup = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!fullName || !email || !password || !departmentId) {
      toast.error("Please fill in all required fields.");
      return;
    }

    setLoading(true);
    setError(null);
    try {
      const result = await apiFetch<{ access_token: string; token_type: string }>(
        "/auth/signup",
        {
          method: "POST",
          body: JSON.stringify({
            full_name: fullName,
            email,
            password,
            department_id: Number(departmentId),
            designation: designation || "Sustainability Advocate",
          }),
        }
      );

      // Store token and redirect — user is immediately logged in
      sessionStorage.setItem("token", result.access_token);
      toast.success("Account created! Welcome to EcoSphere 🌿");
      window.location.href = "/";
    } catch (err: any) {
      setError(err.message || "Registration failed.");
      toast.error(err.message || "Signup failed.");
    } finally {
      setLoading(false);
    }
  };

  const resetForm = () => {
    setEmail("");
    setPassword("");
    setFullName("");
    setDepartmentId("");
    setDesignation("Sustainability Advocate");
    setError(null);
  };

  const inputClass =
    "mt-1 block h-10 w-full rounded-lg border border-border bg-background px-3 font-body text-sm text-foreground focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary";

  const labelClass =
    "block font-body text-xs font-semibold uppercase tracking-wider text-muted-foreground";

  return (
    <div className="flex min-h-screen items-center justify-center bg-background px-4 py-12">
      <Card hover={false} className="w-full max-w-md p-8" accent="primary">
        <div className="flex flex-col items-center text-center">
          <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-primary text-primary-foreground mb-4">
            <Leaf className="h-6 w-6" />
          </div>
          <h1 className="font-display text-3xl font-bold tracking-tight text-foreground">
            {isRegister ? "Create account" : "Welcome back"}
          </h1>
          <p className="mt-2 font-body text-sm text-muted-foreground">
            {isRegister
              ? "Join the EcoSphere sustainability platform"
              : "Sign in to your EcoSphere portal"}
          </p>
        </div>

        <form
          onSubmit={isRegister ? handleSignup : handleLogin}
          className="mt-8 space-y-5"
        >
          {error && (
            <div className="rounded-lg bg-danger/10 p-3 text-sm text-danger font-body">
              {error}
            </div>
          )}

          <div className="space-y-4">
            {/* Register-only: Full Name */}
            {isRegister && (
              <div>
                <label htmlFor="fullName" className={labelClass}>
                  Full Name
                </label>
                <input
                  id="fullName"
                  type="text"
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  required
                  className={inputClass}
                  placeholder="Jane Doe"
                />
              </div>
            )}

            {/* Email */}
            <div>
              <label htmlFor="email" className={labelClass}>
                Email address
              </label>
              <input
                id="email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                className={inputClass}
                placeholder="you@ecosphere.com"
              />
            </div>

            {/* Password */}
            <div>
              <label htmlFor="password" className={labelClass}>
                Password
              </label>
              <input
                id="password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                minLength={6}
                className={inputClass}
                placeholder="••••••••"
              />
            </div>

            {/* Register-only: Department */}
            {isRegister && (
              <div>
                <label htmlFor="department" className={labelClass}>
                  Department
                </label>
                <select
                  id="department"
                  value={departmentId}
                  onChange={(e) => setDepartmentId(Number(e.target.value))}
                  required
                  className={inputClass}
                >
                  <option value="" disabled>
                    Select your department
                  </option>
                  {departments.map((dept) => (
                    <option key={dept.id} value={dept.id}>
                      {dept.name} ({dept.code})
                    </option>
                  ))}
                </select>
              </div>
            )}

            {/* Register-only: Designation */}
            {isRegister && (
              <div>
                <label htmlFor="designation" className={labelClass}>
                  Designation
                </label>
                <input
                  id="designation"
                  type="text"
                  value={designation}
                  onChange={(e) => setDesignation(e.target.value)}
                  className={inputClass}
                  placeholder="Sustainability Advocate"
                />
              </div>
            )}
          </div>

          <Button
            type="submit"
            variant="primary"
            className="w-full h-12 text-sm font-semibold flex items-center justify-center gap-2"
            disabled={loading}
          >
            {isRegister ? (
              <>
                <UserPlus className="h-4 w-4" />
                {loading ? "Creating account..." : "Create account"}
              </>
            ) : (
              <>
                <LogIn className="h-4 w-4" />
                {loading ? "Signing in..." : "Sign in"}
              </>
            )}
          </Button>
        </form>

        {/* Toggle link */}
        <div className="mt-6 text-center">
          <button
            type="button"
            onClick={() => {
              setIsRegister(!isRegister);
              resetForm();
            }}
            className="font-body text-sm text-primary hover:text-primary/80 underline-offset-4 hover:underline transition-colors"
          >
            {isRegister
              ? "Already have an account? Sign in"
              : "Don't have an account? Sign up"}
          </button>
        </div>
      </Card>
    </div>
  );
}
