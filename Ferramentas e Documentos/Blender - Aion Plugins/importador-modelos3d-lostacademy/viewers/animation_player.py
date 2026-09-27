"""
Animation Player & Timeline Transport Controls.
Controls real-time playback, scrubbing, looping, and frame stepping directly from the Aion Model Library UI.
"""

from __future__ import annotations
import bpy


class AnimationPlayer:
    """Controls scene timeline animation playback."""

    @staticmethod
    def play() -> None:
        """Starts real-time timeline animation playback."""
        if not bpy.context.screen.is_animation_playing:
            bpy.ops.screen.animation_play()

    @staticmethod
    def pause() -> None:
        """Pauses animation playback."""
        if bpy.context.screen.is_animation_playing:
            bpy.ops.screen.animation_play()

    @staticmethod
    def stop() -> None:
        """Stops playback and rewinds to frame start."""
        if bpy.context.screen.is_animation_playing:
            bpy.ops.screen.animation_play()
        bpy.context.scene.frame_set(bpy.context.scene.frame_start)

    @staticmethod
    def restart() -> None:
        """Rewinds to beginning and starts playing."""
        bpy.context.scene.frame_set(bpy.context.scene.frame_start)
        if not bpy.context.screen.is_animation_playing:
            bpy.ops.screen.animation_play()

    @staticmethod
    def step_frame(delta: int = 1) -> None:
        """Steps forward or backward by delta frames."""
        curr = bpy.context.scene.frame_current
        target = max(
            bpy.context.scene.frame_start,
            min(bpy.context.scene.frame_end, curr + delta),
        )
        bpy.context.scene.frame_set(target)

    @staticmethod
    def set_frame_range(start: int, end: int) -> None:
        """Sets the timeline active frame range."""
        bpy.context.scene.frame_start = start
        bpy.context.scene.frame_end = max(start + 1, end)

    @staticmethod
    def is_playing() -> bool:
        """Returns True if the timeline is currently playing."""
        return bool(getattr(bpy.context.screen, "is_animation_playing", False))
