import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { api } from "@/lib/api";
import { uploadFile } from "@/lib/upload";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { toast } from "@/hooks/use-toast";
import { Loader2, Upload } from "lucide-react";
import { PageSkeleton } from "@/components/shared/Skeletons";

export default function ProfileSettings() {
    const navigate = useNavigate();
    const queryClient = useQueryClient();
    const [avatarFile, setAvatarFile] = useState<File | null>(null);
    const [avatarPreview, setAvatarPreview] = useState<string | null>(null);

    const { data: profile, isLoading } = useQuery({
        queryKey: ["me"],
        queryFn: () => api.getMe(),
    });

    const [formData, setFormData] = useState({
        display_name: profile?.display_name || "",
        bio: profile?.bio || "",
        handle: profile?.handle || "",
    });

    // Update form when profile loads
    useState(() => {
        if (profile) {
            setFormData({
                display_name: profile.display_name,
                bio: profile.bio || "",
                handle: profile.handle,
            });
        }
    });

    const updateMutation = useMutation({
        mutationFn: async (data: typeof formData & { avatar_key?: string }) => {
            return api.updateMe(data);
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["me"] });
            toast({ title: "Profile updated successfully" });
            navigate(`/u/${formData.handle}`);
        },
        onError: (error: any) => {
            toast({
                title: "Failed to update profile",
                description: error?.error?.message || "Please try again",
                variant: "destructive",
            });
        },
    });

    const handleAvatarChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (file) {
            // Validate file type
            if (!file.type.startsWith("image/")) {
                toast({
                    title: "Invalid file type",
                    description: "Please select an image file",
                    variant: "destructive",
                });
                return;
            }

            // Validate file size (2MB max)
            if (file.size > 2 * 1024 * 1024) {
                toast({
                    title: "File too large",
                    description: "Avatar must be less than 2MB",
                    variant: "destructive",
                });
                return;
            }

            setAvatarFile(file);
            const reader = new FileReader();
            reader.onloadend = () => {
                setAvatarPreview(reader.result as string);
            };
            reader.readAsDataURL(file);
        }
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();

        // Validate handle format
        const handleRegex = /^[a-zA-Z0-9_]{3,30}$/;
        if (!handleRegex.test(formData.handle)) {
            toast({
                title: "Invalid handle",
                description: "Handle must be 3-30 characters (alphanumeric and underscore only)",
                variant: "destructive",
            });
            return;
        }

        let avatar_key: string | undefined;

        // Upload avatar if changed
        if (avatarFile) {
            try {
                avatar_key = await uploadFile(avatarFile, "avatar");
            } catch (error) {
                toast({
                    title: "Failed to upload avatar",
                    description: "Please try again",
                    variant: "destructive",
                });
                return;
            }
        }

        updateMutation.mutate({
            ...formData,
            ...(avatar_key && { avatar_key }),
        });
    };

    if (isLoading) return <PageSkeleton />;

    return (
        <div className="max-w-2xl mx-auto px-4 py-8">
            <Card>
                <CardHeader>
                    <CardTitle>Profile Settings</CardTitle>
                    <CardDescription>Update your profile information</CardDescription>
                </CardHeader>
                <CardContent>
                    <form onSubmit={handleSubmit} className="space-y-6">
                        {/* Avatar */}
                        <div className="space-y-2">
                            <Label>Avatar</Label>
                            <div className="flex items-center gap-4">
                                {avatarPreview || profile?.avatar_url ? (
                                    <img
                                        src={avatarPreview || profile?.avatar_url}
                                        alt="Avatar preview"
                                        className="w-20 h-20 rounded-full object-cover"
                                    />
                                ) : (
                                    <div className="w-20 h-20 rounded-full bg-secondary flex items-center justify-center text-2xl font-medium text-secondary-foreground">
                                        {formData.display_name.charAt(0) || "?"}
                                    </div>
                                )}
                                <div>
                                    <Input
                                        id="avatar"
                                        type="file"
                                        accept="image/*"
                                        onChange={handleAvatarChange}
                                        className="hidden"
                                    />
                                    <Label htmlFor="avatar" className="cursor-pointer">
                                        <Button type="button" variant="outline" size="sm" asChild>
                                            <span>
                                                <Upload className="h-4 w-4 mr-2" />
                                                Upload Avatar
                                            </span>
                                        </Button>
                                    </Label>
                                    <p className="text-xs text-muted-foreground mt-1">
                                        Max 2MB. JPEG, PNG, WebP, or GIF
                                    </p>
                                </div>
                            </div>
                        </div>

                        {/* Display Name */}
                        <div className="space-y-2">
                            <Label htmlFor="display_name">Display Name</Label>
                            <Input
                                id="display_name"
                                value={formData.display_name}
                                onChange={(e) =>
                                    setFormData({ ...formData, display_name: e.target.value })
                                }
                                placeholder="Your display name"
                                required
                            />
                        </div>

                        {/* Handle */}
                        <div className="space-y-2">
                            <Label htmlFor="handle">Handle</Label>
                            <div className="flex items-center gap-2">
                                <span className="text-muted-foreground">@</span>
                                <Input
                                    id="handle"
                                    value={formData.handle}
                                    onChange={(e) =>
                                        setFormData({ ...formData, handle: e.target.value })
                                    }
                                    placeholder="username"
                                    pattern="[a-zA-Z0-9_]{3,30}"
                                    required
                                />
                            </div>
                            <p className="text-xs text-muted-foreground">
                                3-30 characters. Letters, numbers, and underscores only.
                            </p>
                        </div>

                        {/* Bio */}
                        <div className="space-y-2">
                            <Label htmlFor="bio">Bio</Label>
                            <Textarea
                                id="bio"
                                value={formData.bio}
                                onChange={(e) =>
                                    setFormData({ ...formData, bio: e.target.value })
                                }
                                placeholder="Tell us about yourself"
                                rows={4}
                            />
                        </div>

                        {/* Actions */}
                        <div className="flex gap-2 justify-end">
                            <Button
                                type="button"
                                variant="outline"
                                onClick={() => navigate(-1)}
                                disabled={updateMutation.isPending}
                            >
                                Cancel
                            </Button>
                            <Button type="submit" disabled={updateMutation.isPending}>
                                {updateMutation.isPending && (
                                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                                )}
                                Save Changes
                            </Button>
                        </div>
                    </form>
                </CardContent>
            </Card>
        </div>
    );
}
