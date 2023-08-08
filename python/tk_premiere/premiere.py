# Copyright 2023 GPL Solutions, LLC.  All rights reserved.
#
# Use of this software is subject to the terms of the GPL Solutions license
# agreement provided at the time of installation or download, or which otherwise
# accompanies this software in either electronic or hard copy form.
#
import os
from enum import IntEnum

import sgtk
from sgtk.util.filesystem import ensure_folder_exists


class ItemType(IntEnum):
    """
    Mapping for Adobe ProjectItem types.
    """
    CLIP = 1  # A clip
    BIN = 2  # A bin
    ROOT = 3  # Root of the project
    FILE = 4  # A file


class PremiereItem(object):
    """
    Base class for objects handling Premiere objects.
    """
    def __init__(self, item):
        """
        Instantiate a new :class:`PremiereItem` from the given item.

        :param item: A Premiere object returned by the Adobe integration
                              as a :class:`ProxyWrapper`
        """
        super(PremiereItem, self).__init__()
        self._item = item

    @property
    def item(self):
        """
        Return the item associated with this instance.

        :returns: A Premiere ProjectItem.
        """
        return self._item

    @property
    def name(self):
        """
        Return the name of this item.

        :returns: A string.
        """
        return self._item.name

    @property
    def node_id(self):
        """
        Return the internal ID of this Premiere object.

        :returns: A string.
        """
        return self._item.nodeId


class PremiereProject(PremiereItem):
    """
    A class to handle Premiere projects.
    """

    @classmethod
    def get_current_project(cls):
        """
        Return the current Premiere project, if any.

        :returns: A :class:`PremiereProject`.
        :raises ValueError: If no current project can be found.
        """
        engine = sgtk.platform.current_engine()
        project = engine.adobe.app.project
        if not project:
            raise ValueError("No current Premiere project")

        return cls(project)

    def __init__(self, project):
        """
        Instantiate a new :class:`PremiereProject` for the given Premiere project.

        ..see:: https://ppro-scripting.docsforadobe.dev/general/project.html

        :param project: A Premiere Project returned by the Adobe integration
                        as a :class:`ProxyWrapper`.
        """
        super(PremiereProject, self).__init__(project)

    @property
    def path(self):
        """
        Return the path on the filesystem of this project.

        :returns: A string.
        """
        return self._item.path

    @property
    def node_id(self):
        """
        Return the internal ID of the Premiere Project root item.

        :returns: A string.
        """
        # The Project itself is not a Premiere ProjectItem but its
        # root item is.
        return self._item.rootItem.nodeId

    @property
    def bins(self):
        """
        Iterate over all bins in this project.

        :yields: :class:`PremiereBin`.
        """
        # The top project item is also a bin.
        bins = [self._item.rootItem]
        while bins:
            bin = bins.pop()
            # Iterating over children directly sometimes
            # goes into infinite loops or returns ``None``
            # results, safer to iterate over the number
            # of children.
            for i in range(bin.children.numItems):
                child = bin.children[i]
                if child and child.type == ItemType.BIN:
                    bins.append(child)
            yield PremiereBin(bin)

    @property
    def clips(self):
        """
        Iterate over all clips in this project.

        :yields: :class:`PremiereClip`.
        """
        for bin in self.bins:
            for clip in bin.clips:
                yield clip

    @property
    def timelines(self):
        """
        Iterate over timelines for this project.

        :yields: :class:`PremiereTimeline`.
        """
        for sequence in self._item.sequences:
            yield PremiereTimeline(sequence)

    @property
    def current_timeline(self):
        """
        Return the active timeline for this project, if there is one.

        :returns: A :class:`PremiereTimeline` or ``None``.
        """
        sequence = self._item.activeSequence
        if sequence:
            return PremiereTimeline(sequence)
        return None

    def get_clip_by_id(self, node_id):
        """
        Return the clip with the given node id.

        :returns: A :class:`PremiereClip` or ``None``.
        """
        for clip in self.clips:
            if clip.node_id == node_id:
                return clip
        return None

    def save(self, path=None):
        """
        Save this project in place or to the given path.

        :param str path: Optional, the target file path.
        :returns: The project's path.
        """

        if path is None:
            self._item.save()
        else:
            # Premiere won't ensure that the folder is created when saving,
            # so we must make sure it exists
            ensure_folder_exists(os.path.dirname(path))
            self._item.saveAs(path)
        return self.path


class PremiereTimeline(PremiereItem):
    """
    A class to handle Premiere timelines (sequences).
    """

    def __init__(self, timeline):
        """
        Instantiate a PremiereTimeline.

        ..see:: https://ppro-scripting.docsforadobe.dev/sequence/sequence.html

        :param timeline: A Premiere Sequence object returned by the Adobe integration
                        as a :class:`ProxyWrapper`.
        """
        super(PremiereTimeline, self).__init__(timeline)

    @property
    def node_id(self):
        """
        Return the internal ID of the Premiere Sequence project item.

        :returns: A string.
        """
        # The Project itself is not a Premiere ProjectItem but its
        # root item is.
        return self._item.projectItem.nodeId

    @property
    def video_tracks(self):
        """
        Iterate over all video tracks within this timeline.

        :yields: :class:`PremiereTrack` instances.
        """
        # Iterating over tracks directly sometimes
        # goes into infinite loops or returns ``None``
        # results, safer to iterate over the number
        # of tracks.
        for i in range(self._item.videoTracks.numTracks):
            track = self._item.videoTracks[i]
            yield PremiereTrack(track)

    @property
    def audio_tracks(self):
        """
        Iterate over  all audio tracks within this timeline.

        :yields: :class:`PremiereTrack` instances.
        """
        # Iterating over tracks directly sometimes
        # goes into infinite loops or returns ``None``
        # results, safer to iterate over the number
        # of tracks.
        for i in range(self._item.audioTracks.numTracks):
            track = self._item.audioTracks[i]
            yield PremiereTrack(track)

    @property
    def tracks(self):
        """
        Iterate over tracks within this timeline.

        :yields: :class:`PremiereTrack` instances.
        """
        for track in self.video_tracks:
            yield track
        for track in self.audio_tracks:
            yield track

    @property
    def clips(self):
        """
        Iterate over all clips from all tracks in this timeline.

        :yields: :class:`PremiereTrackClip` instances.
        """
        for track in self.tracks:
            for clip in track.clips:
                yield clip


class PremiereTrack(PremiereItem):
    """
    A class to handle Premiere Tracks.
    """
    def __init__(self, track):
        """
        Instantiate a PremiereTrack.

        ..see:: https://ppro-scripting.docsforadobe.dev/sequence/track.html#track

        :param track: A Premiere Track object returned by the Adobe integration
                        as a :class:`ProxyWrapper`.
        """
        super(PremiereTrack, self).__init__(track)

    @property
    def clips(self):
        """
        Iterate over all clips in this track.

        :yields: :class:`PremiereTrackClip` instances.
        """
        # Iterating over clips directly sometimes
        # goes into infinite loops or returns ``None``
        # results, safer to iterate over the number
        # of clips.
        for i in range(self._item.clips.numItems):
            clip = self._item.clips[i]
            yield PremiereTrackClip(clip)


class PremiereTrackClip(PremiereItem):
    """
    A class to handle Premiere Tracks Clips.
    """
    def __init__(self, track_item):
        """
        Instantiate a PremiereTrackClip.

        ..see:: https://ppro-scripting.docsforadobe.dev/item/trackitem.html

        :param clip: A Premiere TrackItem object returned by the Adobe integration
                        as a :class:`ProxyWrapper`.
        """
        super(PremiereTrackClip, self).__init__(track_item)
        self._clip = PremiereClip(self._item.projectItem)

    @property
    def clip(self):
        """
        Return the clip providing media for this track clip.

        :returns: A :class:`PremiereClip` instance.
        """
        return self._clip


class PremiereBin(PremiereItem):
    """
    A class to handle Premiere bins.
    """
    def __init__(self, bin):
        """
        Instantiate a PremiereBin.

        ..see:: https://ppro-scripting.docsforadobe.dev/item/projectitem.html

        :param bin: A Premiere ProjectItem object returned by the Adobe integration
                        as a :class:`ProxyWrapper`.
        """
        super(PremiereBin, self).__init__(bin)

    @property
    def clips(self):
        """
        Iterate over all clips in this bin

        :yields: :class:`PremiereClip`.
        """
        # Iterating over children directly sometimes
        # goes into infinite loops or returns ``None``
        # results, safer to iterate over the number
        # of children.
        for i in range(self._item.children.numItems):
            child = self._item.children[i]
            # Sequences are clips as well.
            if child.type == ItemType.CLIP and not child.isSequence():
                yield PremiereClip(child)


class PremiereClip(PremiereItem):
    """
    A class to handle Premiere clips.
    """
    def __init__(self, clip):
        """
        Instantiate a PremiereClip.

        ..see:: https://ppro-scripting.docsforadobe.dev/item/projectitem.html

        :param bin: A Premiere ProjectItem object returned by the Adobe integration
                        as a :class:`ProxyWrapper`.
        """
        super(PremiereClip, self).__init__(clip)

    @property
    def media_path(self):
        """
        Returns the media path associated with this clip.

        :returns: A string.
        """
        return self._item.getMediaPath()

    @media_path.setter
    def media_path(self, path):
        """
        Set the media path associated with this clip.

        :param path: File path to the media, as a string.
        """
        if not self._item.canChangeMediaPath():
            raise ValueError("Media path can't be changed on %s" % self.name)
        self._item.changeMediaPath(path)
