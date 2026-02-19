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

interface BlockConfirmDialogProps {
    open: boolean;
    onOpenChange: (open: boolean) => void;
    onConfirm: () => void;
    userName: string;
    isBlocking: boolean;
}

export function BlockConfirmDialog({
    open,
    onOpenChange,
    onConfirm,
    userName,
    isBlocking,
}: BlockConfirmDialogProps) {
    if (!isBlocking) {
        // For unblocking, just confirm immediately without dialog
        return null;
    }

    return (
        <AlertDialog open={open} onOpenChange={onOpenChange}>
            <AlertDialogContent>
                <AlertDialogHeader>
                    <AlertDialogTitle>Block {userName}?</AlertDialogTitle>
                    <AlertDialogDescription className="space-y-2">
                        <p>
                            Blocking this user will:
                        </p>
                        <ul className="list-disc list-inside space-y-1 text-sm">
                            <li>Hide their content from your feeds</li>
                            <li>Prevent them from following you</li>
                            <li>Remove them from your followers if they follow you</li>
                            <li>Hide their stories, whispers, and comments</li>
                        </ul>
                        <p className="mt-3">
                            You can unblock them anytime from their profile.
                        </p>
                    </AlertDialogDescription>
                </AlertDialogHeader>
                <AlertDialogFooter>
                    <AlertDialogCancel>Cancel</AlertDialogCancel>
                    <AlertDialogAction onClick={onConfirm} className="bg-destructive text-destructive-foreground hover:bg-destructive/90">
                        Block User
                    </AlertDialogAction>
                </AlertDialogFooter>
            </AlertDialogContent>
        </AlertDialog>
    );
}
