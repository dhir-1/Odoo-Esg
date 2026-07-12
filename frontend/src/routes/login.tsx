import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "@/contexts/auth-context";
import { Card } from "@/components/ecosphere/card";
import { Button } from "@/components/ecosphere/button";
import { apiFetch } from "@/lib/api-client";
import { toast } from "sonner";
import { Leaf, UserPlus, LogIn } from "lucide-react";
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

interface DepartmentOption {
  id: number;
  name: string;
  code: string;
  status: string;
}

export function LoginPage() {
  const { login } = useAuth();
  const navigate = useNavigate();

  const [mode, setMode] = useState<"login" | "register" | "reset">("login");
  const [confirmLoginOpen, setConfirmLoginOpen] = useState(false);

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [fullName, setFullName] = useState("");
  const [departmentId, setDepartmentId] = useState<number | "">("");
  const [designation, setDesignation] = useState("Sustainability Advocate");
  const [departments, setDepartments] = useState<DepartmentOption[]>([]);
  const [resetPassword, setResetPassword] = useState("");
  const [resetConfirmPassword, setResetConfirmPassword] = useState("");

  useEffect(() => {
    if (mode === "register" && departments.length === 0) {
      fetchDepartments();
    }
  }, [mode, departments.length]);

  const fetchDepartments = async () => {
    try {
      const baseUrl = (import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api/v1").replace(/\/$/, "");
      const res = await fetch(`${baseUrl}/departments/public`);
      if (res.ok) {
        const data = await res.json();
        setDepartments(data.filter((d: DepartmentOption) => d.status === "Active"));
      }
    } catch {
      // Demo fallback only.
    }
  };

  const performLogin = async () => {
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

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email || !password) {
      toast.error("Please enter email and password.");
      return;
    }
    setConfirmLoginOpen(true);
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
      const result = await apiFetch<{ access_token: string; token_type: string }>("/auth/signup", {
        method: "POST",
        body: JSON.stringify({
          full_name: fullName,
          email,
          password,
          department_id: Number(departmentId),
          designation: designation || "Sustainability Advocate",
        }),
      });

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

  const handlePasswordReset = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email) {
      toast.error("Please enter your email address first.");
      return;
    }
    if (!resetPassword || !resetConfirmPassword) {
      toast.error("Please enter and confirm your new password.");
      return;
    }
    if (resetPassword !== resetConfirmPassword) {
      toast.error("Passwords do not match.");
      return;
    }
    toast.success("Password reset request captured for this demo flow.");
    setMode("login");
    setResetPassword("");
    setResetConfirmPassword("");
  };

  const resetForm = () => {
    setEmail("");
    setPassword("");
    setFullName("");
    setDepartmentId("");
    setDesignation("Sustainability Advocate");
    setResetPassword("");
    setResetConfirmPassword("");
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
          <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-xl bg-primary text-primary-foreground">
            <Leaf className="h-6 w-6" />
          </div>
          <h1 className="font-display text-3xl font-bold tracking-tight text-foreground">
            {mode === "register" ? "Create account" : mode === "reset" ? "Reset password" : "Welcome back"}
          </h1>
          <p className="mt-2 font-body text-sm text-muted-foreground">
            {mode === "register"
              ? "Join the EcoSphere sustainability platform"
              : mode === "reset"
                ? "Request a password reset for your EcoSphere account"
                : "Sign in to your EcoSphere portal"}
          </p>
        </div>

        <form
          onSubmit={mode === "register" ? handleSignup : mode === "reset" ? handlePasswordReset : handleLogin}
          className="mt-8 space-y-5"
        >
          {error && (
            <div className="rounded-lg bg-danger/10 p-3 text-sm text-danger font-body">
              {error}
            </div>
          )}

          <div className="space-y-4">
            {mode === "register" && (
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

            {mode !== "reset" ? (
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
            ) : (
              <>
                <div>
                  <label htmlFor="resetPassword" className={labelClass}>
                    New password
                  </label>
                  <input
                    id="resetPassword"
                    type="password"
                    value={resetPassword}
                    onChange={(e) => setResetPassword(e.target.value)}
                    required
                    minLength={6}
                    className={inputClass}
                    placeholder="Create a new password"
                  />
                </div>
                <div>
                  <label htmlFor="resetConfirmPassword" className={labelClass}>
                    Confirm new password
                  </label>
                  <input
                    id="resetConfirmPassword"
                    type="password"
                    value={resetConfirmPassword}
                    onChange={(e) => setResetConfirmPassword(e.target.value)}
                    required
                    minLength={6}
                    className={inputClass}
                    placeholder="Confirm new password"
                  />
                </div>
              </>
            )}

            {mode === "register" && (
              <>
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
              </>
            )}
          </div>

          <Button
            type="submit"
            variant="primary"
            className="flex h-12 w-full items-center justify-center gap-2 text-sm font-semibold"
            disabled={loading}
          >
            {mode === "register" ? (
              <>
                <UserPlus className="h-4 w-4" />
                {loading ? "Creating account..." : "Create account"}
              </>
            ) : mode === "reset" ? (
              "Send reset request"
            ) : (
              <>
                <LogIn className="h-4 w-4" />
                {loading ? "Signing in..." : "Sign in"}
              </>
            )}
          </Button>
        </form>

        <div className="mt-6 space-y-2 text-center">
          {mode !== "reset" && (
            <button
              type="button"
              onClick={() => {
                setMode(mode === "register" ? "login" : "register");
                resetForm();
              }}
              className="font-body text-sm text-primary underline-offset-4 transition-colors hover:underline hover:text-primary/80"
            >
              {mode === "register" ? "Already have an account? Sign in" : "Don't have an account? Sign up"}
            </button>
          )}
          <button
            type="button"
            onClick={() => setMode(mode === "reset" ? "login" : "reset")}
            className="block w-full font-body text-sm text-muted-foreground underline-offset-4 transition-colors hover:underline hover:text-foreground"
          >
            {mode === "reset" ? "Back to sign in" : "Forgot password?"}
          </button>
        </div>

        <AlertDialog open={confirmLoginOpen} onOpenChange={setConfirmLoginOpen}>
          <AlertDialogContent>
            <AlertDialogHeader>
              <AlertDialogTitle>Proceed with sign in?</AlertDialogTitle>
              <AlertDialogDescription>
                Make sure this is the account you want to enter. You can still cancel and edit the fields.
              </AlertDialogDescription>
            </AlertDialogHeader>
            <AlertDialogFooter>
              <AlertDialogCancel>Cancel</AlertDialogCancel>
              <AlertDialogAction
                onClick={async () => {
                  setConfirmLoginOpen(false);
                  await performLogin();
                }}
              >
                Continue
              </AlertDialogAction>
            </AlertDialogFooter>
          </AlertDialogContent>
        </AlertDialog>
      </Card>
    </div>
  );
}
