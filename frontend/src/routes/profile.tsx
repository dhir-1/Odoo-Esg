import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Shield, LogOut, UserCircle2 } from "lucide-react";
import { toast } from "sonner";
import { useAuth } from "@/contexts/auth-context";
import { apiFetch } from "@/lib/api-client";
import { Card } from "@/components/ecosphere/card";
import { Button } from "@/components/ecosphere/button";

export function ProfilePage() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [loading, setLoading] = useState(false);

  const inputClass =
    "mt-1 block h-10 w-full rounded-lg border border-border bg-background px-3 font-body text-sm text-foreground focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary";

  const handleChangePassword = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!currentPassword || !newPassword || !confirmPassword) {
      toast.error("Please fill in all password fields.");
      return;
    }
    if (newPassword !== confirmPassword) {
      toast.error("New passwords do not match.");
      return;
    }

    setLoading(true);
    try {
      await apiFetch("/auth/change-password", {
        method: "POST",
        body: JSON.stringify({
          current_password: currentPassword,
          new_password: newPassword,
        }),
      });
      toast.success("Password updated successfully.");
      setCurrentPassword("");
      setNewPassword("");
      setConfirmPassword("");
    } catch (err: any) {
      toast.error(err.message || "Failed to update password.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="mx-auto max-w-4xl space-y-6 font-sans text-foreground">
      <div>
        <h1 className="font-display text-3xl font-bold">Profile summary</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Review your account details and change your password here.
        </p>
      </div>

      <div className="grid gap-6 lg:grid-cols-[1.2fr_0.8fr]">
        <Card hover={false} className="p-6">
          <div className="flex items-center gap-3">
            <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-primary text-primary-foreground">
              <UserCircle2 className="h-6 w-6" />
            </div>
            <div>
              <h2 className="font-display text-xl font-semibold">{user?.full_name || "Guest User"}</h2>
              <p className="text-sm text-muted-foreground">{user?.designation || user?.role || "Visitor"}</p>
            </div>
          </div>

          <div className="mt-6 grid gap-3 text-sm">
            <div className="rounded-lg border border-border bg-muted/30 p-4">
              <p className="text-xs uppercase tracking-wider text-muted-foreground">Email</p>
              <p className="mt-1 font-medium">{user?.email || "Not available"}</p>
            </div>
            <div className="rounded-lg border border-border bg-muted/30 p-4">
              <p className="text-xs uppercase tracking-wider text-muted-foreground">Role</p>
              <p className="mt-1 font-medium">{user?.role || "Visitor"}</p>
            </div>
            <div className="rounded-lg border border-border bg-muted/30 p-4">
              <p className="text-xs uppercase tracking-wider text-muted-foreground">Department ID</p>
              <p className="mt-1 font-medium">{user?.department_id ?? "Not assigned"}</p>
            </div>
            <div className="rounded-lg border border-border bg-muted/30 p-4">
              <p className="text-xs uppercase tracking-wider text-muted-foreground">XP Points</p>
              <p className="mt-1 font-medium">{user?.xp_points ?? 0}</p>
            </div>
          </div>
        </Card>

        <Card hover={false} className="p-6">
          <div className="flex items-center gap-3">
            <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-secondary text-secondary-foreground">
              <Shield className="h-6 w-6" />
            </div>
            <div>
              <h2 className="font-display text-xl font-semibold">Reset password</h2>
              <p className="text-sm text-muted-foreground">Update your password for the Soteria workspace.</p>
            </div>
          </div>

          <form onSubmit={handleChangePassword} className="mt-6 space-y-4">
            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                Current password
              </label>
              <input
                type="password"
                value={currentPassword}
                onChange={(e) => setCurrentPassword(e.target.value)}
                className={inputClass}
              />
            </div>
            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                New password
              </label>
              <input
                type="password"
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                minLength={6}
                className={inputClass}
              />
            </div>
            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                Confirm new password
              </label>
              <input
                type="password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                minLength={6}
                className={inputClass}
              />
            </div>

            <div className="flex flex-col gap-2 pt-2 sm:flex-row">
              <Button type="submit" variant="primary" className="flex-1" disabled={loading}>
                {loading ? "Saving..." : "Update password"}
              </Button>
              <Button
                type="button"
                variant="outline"
                className="flex-1 gap-2"
                onClick={() => {
                  logout();
                  navigate("/login");
                }}
              >
                <LogOut className="h-4 w-4" />
                Log out
              </Button>
            </div>
          </form>
        </Card>
      </div>
    </div>
  );
}
