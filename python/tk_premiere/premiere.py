# Copyright 2023 GPL Solutions, LLC.  All rights reserved.
#
# Use of this software is subject to the terms of the GPL Solutions license
# agreement provided at the time of installation or download, or which otherwise
# accompanies this software in either electronic or hard copy form.
#
from enum import IntEnum
import os
import re

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

    @name.setter
    def name(self, name):
        """
        Set the name of this item
        """
        self._item.name = name

    @property
    def node_id(self):
        """
        Return the internal ID of this Premiere object.

        :returns: A string.
        """
        return self._item.nodeId

    def get_meta_data(self, property):
        """
        Return the meta data value for the given property.

        :param property: A meta data property name, like 'myproperty' or 'Column.PropertyBool.Hide' for
                         standard meta data properties.
        :returns: The meta data value or ``None``.
        """
        meta_data = self.item.getProjectMetadata()
        # We get something like this, with tags only for properties which have been set:
        # <?xpacket begin="﻿" id="W5M0MpCehiHzreSzNTczkc9d"?>
        # <x:xmpmeta xmlns:x="adobe:ns:meta/" x:xmptk="Adobe XMP Core 7.1-c000 79.b0f8be9, 2021/12/08-19:11:22        ">
        #    <rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">
        #       <rdf:Description rdf:about=""
        #             xmlns:premierePrivateProjectMetaData="http://ns.adobe.com/premierePrivateProjectMetaData/1.0/">
        #          <premierePrivateProjectMetaData:Column.Intrinsic.Name>blah</premierePrivateProjectMetaData:Column.Intrinsic.Name>
        #          <premierePrivateProjectMetaData:Column.PropertyText.Label>BE.Prefs.LabelColors.7</premierePrivateProjectMetaData:Column.PropertyText.Label>
        #          <premierePrivateProjectMetaData:Column.Intrinsic.MediaType>Bin</premierePrivateProjectMetaData:Column.Intrinsic.MediaType>
        #          <premierePrivateProjectMetaData:Column.PropertyBool.Good>True</premierePrivateProjectMetaData:Column.PropertyBool.Good>
        #          <premierePrivateProjectMetaData:Column.PropertyBool.Hide>False</premierePrivateProjectMetaData:Column.PropertyBool.Hide>
        #          <premierePrivateProjectMetaData:Column.PropertyBool.PropagatedHide>False</premierePrivateProjectMetaData:Column.PropertyBool.PropagatedHide>
        #          <premierePrivateProjectMetaData:myprop>test</premierePrivateProjectMetaData:myprop>
        #       </rdf:Description>
        #    </rdf:RDF>
        # </x:xmpmeta>
        # <?xpacket end="w"?>
        m = re.search(
            r"<premierePrivateProjectMetaData:%s>(.*)</premierePrivateProjectMetaData:%s>" % (property, property),
            meta_data
        )
        if not m:
            # Since we don't get entries for properties which have not been set
            # we can't know if the property exists or not, or is empty.
            # So we return None for the time being...
            return None
        return m.group(1)

    def set_meta_data(self, property, value):
        """
        Set the meta data value for the given property.

        :param property: A meta data property name, like 'myproperty' or 'Column.PropertyBool.Hide' for
                         standard meta data properties.
        :param value: The value to set.
        :returns: The value which was actually set.
        """
        meta_data = self.item.getProjectMetadata()
        # Check if the property is present in the meta data and replace its value
        repl = re.sub(
            r"<premierePrivateProjectMetaData:%s>(.*)</premierePrivateProjectMetaData:%s>" % (property, property),
            r"<premierePrivateProjectMetaData:%s>%s</premierePrivateProjectMetaData:%s>" % (property, value, property),
            meta_data,
        )
        if repl == meta_data:
            # If we didn't find the property, add it to the meta data.
            # Since we pass the name of the property to set, we can just replace any property entry in
            # the meta data string with what we want to set.
            repl = re.sub(
                r"<premierePrivateProjectMetaData:[^<]+>(.*)</premierePrivateProjectMetaData:.*>",
                r"<premierePrivateProjectMetaData:%s>%s</premierePrivateProjectMetaData:%s>" % (property, value, property),
                meta_data,
                1
            )
        # https://ppro-scripting.docsforadobe.dev/item/projectitem.html#projectitem-setprojectmetadata
        self.item.setProjectMetadata(repl, [property])
        return self.get_meta_data(property)


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

    def get_insertion_bin(self):
        """
        Return the insertion bin for this project.
        https://ppro-scripting.docsforadobe.dev/general/project.html#project-getinsertionbin

        :returns: A :class:`PremiereBin`.
        """
        return PremiereBin(self._item.getInsertionBin())

    def get_bin_by_name(self, name):
        """
        Return the bin with the given name from the project root, if any.

        :returns: A :class:`PremiereBin` or ``None``.
        """
        return PremiereBin(self._item.rootItem).get_bin_by_name(name)

    def create_bin(self, name):
        """
        Create a bin with the current name under the project root bin.

        :param str name: The bin name to create.
        :returns: A :class:`PremiereBin`.
        """
        top_bin = self._item.rootItem
        return PremiereBin(top_bin.createBin(name))

    def ensure_bin(self, name):
        """
        Ensure that a bin with the given name exists under the project root bin.

        :param str name: The name of the bin.
        :returns: A :class:`PremiereBin`.
        """
        top_bin = self._item.rootItem
        return PremiereBin(top_bin).ensure_bin(name)

    def ensure_bins_for_path(self, path):
        """
        Ensure that bins exists for the given path.

        :param str path: A bins path, with / as separators.
        :returns: A :class:`PremiereBin`.
        :raises ValueError: For invalid paths.
        """
        parts = [p for p in path.split("/") if p]  # Skip leading, ending and consecutive /
        if not parts:
            raise ValueError("Invalid import bin path %s" % path)
        current_bin = self.ensure_bin(parts[0])
        for part in parts[1:]:
            current_bin = current_bin.ensure_bin(part)
        return current_bin

    def add_meta_data_property(self, name, display_name, property_type):
        """
        Add a property with the given name to the meta data schema.

        .. note:: It is not possible to retrieve the meta data schema so the
                  property is blindly added to the schema. Conflicts with
                  existing properties do not cause errors, but their display
                  name or type is not changed if different.

        :param str name: The name for the property, which acts as its indentifier.
        :param str display_name: The display name for the property, which will be displayed in UIs.
        :param str property_type: The type for the property, e.g. "int", "float", "string", "bool".
        """
        value_type = {
            "int": 0,
            "integer": 0,
            "real": 1,
            "float": 1,
            "str": 2,
            "string": 2,
            "bool": 3,
            "boolean": 3,
        }.get(property_type.lower())

        if value_type is None:
            raise ValueError("Unsupported property type %s" % property_type)
        return self.item.addPropertyToProjectMetadataSchema(
            name,
            display_name,
            value_type
        )

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

    def get_bin_by_name(self, name):
        """
        Return the bin with the given name in this bin, if any.

        :returns: A :class:`PremiereBin` or ``None``.
        """
        for i in range(self._item.children.numItems):
            child = self._item.children[i]
            if child and child.type == ItemType.BIN:
                if child.name == name:
                    return PremiereBin(child)
        return None

    def create_bin(self, name):
        """
        Create a bin with the current name under this bin.

        :param str name: The name of the new bin.
        :returns: A :class:`PremiereBin`.
        """
        return PremiereBin(self._item.createBin(name))

    def ensure_bin(self, name):
        """
        Ensure that a bin with the given name exists under this bin.

        :param str name: The name of the bin.
        :returns: A :class:`PremiereBin`.
        """
        bin = self.get_bin_by_name(name)
        if not bin:
            bin = self.create_bin(name)
        return bin

    def create_clip_from_media(self, media_path):
        """
        Create a clip for the given media file in this bin.

        :param str media_path: Full path to the media file.
        :returns: A :class:`PremiereClip`, the created clip.
        :raises ValueError: If the clip was not created.
        """
        engine = sgtk.platform.current_engine()
        # We can't really rely on importFiles returned value
        # so we count items before doing the import to check
        # if something was added.
        old_count = self._item.children.numItems
        engine.adobe.app.project.importFiles(
            [media_path],
            False,
            self._item,
            False
        )
        if old_count == self._item.children.numItems:
            raise ValueError("Unable to create a clip for %s" % media_path)
        # Assuming here that the new child is added at the end.
        last = self._item.children[self._item.children.numItems - 1]
        if not last or last.type != ItemType.CLIP:
            raise ValueError("Unable to retrieve the created clip for %s" % media_path)
        return PremiereClip(last)


class PremiereClip(PremiereItem):
    """
    A class to handle Premiere clips.
    """
    def __init__(self, clip):
        """
        Instantiate a PremiereClip.

        ..see:: https://ppro-scripting.docsforadobe.dev/item/projectitem.html

        :param clip: A Premiere ProjectItem object returned by the Adobe integration
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
