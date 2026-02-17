import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogFooter,
    DialogHeader,
    DialogTitle,
} from "@/components/ui/dialog";
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
    DropdownMenuSeparator,
    DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { MoreVertical, Edit2, Trash2 } from "lucide-react";
import { toast } from "@/hooks/use-toast";
import type { Shelf } from "@/types";

interface ShelfManagerProps {
    shelf: Shelf;
    onShelfDeleted?: () => void;
}

export function ShelfManager({ shelf, onShelfDeleted }: ShelfManagerProps) {
    const [showRenameDialog, setShowRenameDialog] = useState(false);
    const [showDeleteDialog, setShowDeleteDialog] = useState(false);
    const [newName, setNewName] = useState(shelf.name);
    const queryClient = useQueryClient();

    const renameMutation = useMutation({
        mutationFn: () => api.updateShelf(shelf.id, { name: newName }),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["shelves"] });
            queryClient.invalidateQueries({ queryKey: ["shelf-items", shelf.id] });
            setShowRenameDialog(false);
            toast({ title: "Shelf renamed successfully!" });
        },
        onError: (error: any) => {
            toast({
                title: "Failed to rename shelf",
                description: error?.error?.message || "Please try again",
                variant: "destructive",
            });
        },
    });

    const deleteMutation = useMutation({
        mutationFn: () => api.deleteShelf(shelf.id),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["shelves"] });
            setShowDeleteDialog(false);
            toast({ title: "Shelf deleted successfully!" });
            onShelfDeleted?.();
        },
        onError: (error: any) => {
            toast({
                title: "Failed to delete shelf",
                description: error?.error?.message || "Please try again",
                variant: "destructive",
            });
        },
    });

    const handleRename = (e: React.FormEvent) => {
        e.preventDefault();
        if (newName.trim() && newName !== shelf.name) {
            renameMutation.mutate();
        }
    };

    const handleDelete = () => {
        deleteMutation.mutate();
    };

    return (
        <>
            <DropdownMenu>
                <DropdownMenuTrigger asChild>
                    <Button variant="ghost" size="icon" className="h-8 w-8">
                        <MoreVertical className="h-4 w-4" />
                        <span className="sr-only">Shelf options</span>
                    </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end">
                    <DropdownMenuItem onClick={() => {
                        setNewName(shelf.name);
                        setShowRenameDialog(true);
                    }}>
                        <Edit2 className="h-4 w-4 mr-2" />
                        Rename shelf
                    </DropdownMenuItem>
                    <DropdownMenuSeparator />
                    <DropdownMenuItem
                        onClick={() => setShowDeleteDialog(true)}
                        className="text-destructive focus:text-destructive"
                    >
                        <Trash2 className="h-4 w-4 mr-2" />
                        Delete shelf
                    </DropdownMenuItem>
                </DropdownMenuContent>
            </DropdownMenu>

            {/* Rename Dialog */}
            <Dialog open={showRenameDialog} onOpenChange={setShowRenameDialog}>
                <DialogContent>
                    <DialogHeader>
                        <DialogTitle>Rename shelf</DialogTitle>
                        <DialogDescription>
                            Enter a new name for "{shelf.name}"
                        </DialogDescription>
                    </DialogHeader>
                    <form onSubmit={handleRename}>
                        <div className="space-y-4">
                            <Input
                                value={newName}
                                onChange={(e) => setNewName(e.target.value)}
                                placeholder="Shelf name"
                                maxLength={50}
                                autoFocus
                            />
                        </div>
                        <DialogFooter className="mt-4">
                            <Button
                                type="button"
                                variant="outline"
                                onClick={() => setShowRenameDialog(false)}
                            >
                                Cancel
                            </Button>
                            <Button
                                type="submit"
                                disabled={!newName.trim() || newName === shelf.name || renameMutation.isPending}
                            >
                                {renameMutation.isPending ? "Renaming..." : "Rename"}
                            </Button>
                        </DialogFooter>
                    </form>
                </DialogContent>
            </Dialog>

            {/* Delete Confirmation Dialog */}
            <AlertDialog open={showDeleteDialog} onOpenChange={setShowDeleteDialog}>
                <AlertDialogContent>
                    <AlertDialogHeader>
                        <AlertDialogTitle>Delete shelf?</AlertDialogTitle>
                        <AlertDialogDescription>
                            Are you sure you want to delete "{shelf.name}"? This will remove the shelf but
                            won't delete the stories. This action cannot be undone.
                        </AlertDialogDescription>
                    </AlertDialogHeader>
                    <AlertDialogFooter>
                        <AlertDialogCancel>Cancel</AlertDialogCancel>
                        <AlertDialogAction
                            onClick={handleDelete}
                            disabled={deleteMutation.isPending}
                            className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
                        >
                            {deleteMutation.isPending ? "Deleting..." : "Delete"}
                        </AlertDialogAction>
                    </AlertDialogFooter>
                </AlertDialogContent>
            </AlertDialog>
        </>
    );
}

interface StoryRemovalProps {
    shelfId: string;
    storyId: string;
    storyTitle: string;
    onRemoved?: () => void;
}

export function StoryRemovalButton({ shelfId, storyId, storyTitle, onRemoved }: StoryRemovalProps) {
    const [showConfirm, setShowConfirm] = useState(false);
    const queryClient = useQueryClient();

    const removeMutation = useMutation({
        mutationFn: () => api.removeFromShelf(shelfId, storyId),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["shelves"] });
            queryClient.invalidateQueries({ queryKey: ["shelf-items", shelfId] });
            setShowConfirm(false);
            toast({ title: "Story removed from shelf" });
            onRemoved?.();
        },
        onError: (error: any) => {
            toast({
                title: "Failed to remove story",
                description: error?.error?.message || "Please try again",
                variant: "destructive",
            });
        },
    });

    return (
        <>
            <Button
                variant="ghost"
                size="sm"
                onClick={() => setShowConfirm(true)}
                className="text-muted-foreground hover:text-destructive"
            >
                <Trash2 className="h-4 w-4 mr-1" />
                Remove
            </Button>

            <AlertDialog open={showConfirm} onOpenChange={setShowConfirm}>
                <AlertDialogContent>
                    <AlertDialogHeader>
                        <AlertDialogTitle>Remove from shelf?</AlertDialogTitle>
                        <AlertDialogDescription>
                            Are you sure you want to remove "{storyTitle}" from this shelf? The story
                            itself won't be deleted.
                        </AlertDialogDescription>
                    </AlertDialogHeader>
                    <AlertDialogFooter>
                        <AlertDialogCancel>Cancel</AlertDialogCancel>
                        <AlertDialogAction
                            onClick={() => removeMutation.mutate()}
                            disabled={removeMutation.isPending}
                        >
                            {removeMutation.isPending ? "Removing..." : "Remove"}
                        </AlertDialogAction>
                    </AlertDialogFooter>
                </AlertDialogContent>
            </AlertDialog>
        </>
    );
}
