from io import BytesIO
from xml.etree.ElementTree import Element, ElementTree, SubElement, parse


class POX:
    """Convert Plain Old XML to and from various formats."""

    @classmethod
    def to_dict(cls, xml):
        if isinstance(xml, str):
            xml = xml.encode("utf-8")

        tree = Transform.bytes_to_tree(xml)
        Transform.namespace_to_attr(tree.getroot())

        return XMLToDict.to_dict(tree)

    @classmethod
    def to_bytes(cls, xml_data):
        tree = DictToXML.tree(xml_data)
        return Transform.tree_to_bytes(tree)


class Transform:
    """Transform XML in various ways."""

    @classmethod
    def tree_to_bytes(cls, tree, encoding="utf-8", xml_declaration=True):
        out = BytesIO()
        tree.write(out, encoding=encoding, xml_declaration=xml_declaration)
        return out.getvalue()

    @classmethod
    def bytes_to_tree(cls, bytes_in):
        return parse(BytesIO(bytes_in))

    @classmethod
    def namespace_to_attr(cls, element, namespace=None):
        tag = element.tag
        if tag.startswith("{"):
            split = tag.index("}")
            tag_ns, tag_name = tag[1:split], tag[split + 1 :]

            if tag_ns != namespace:
                element.attrib["xmlns"] = tag_ns
                namespace = tag_ns

            element.tag = tag_name

        for child in element:
            cls.namespace_to_attr(child, namespace)


class XMLToDict:
    """Convert simple XML into a dict."""

    @classmethod
    def to_dict(cls, tree):
        root = tree.getroot()
        return {root.tag: cls._to_dict(root)}

    @classmethod
    def _to_dict(cls, element):
        data = {child.tag: cls._to_dict(child) for child in element}

        if not data:
            return element.text

        if element.attrib:
            data["_attr"] = element.attrib

        return data


class DictToXML:
    """Convert dicts into XML."""

    @classmethod
    def tree(cls, xml_data):
        if len(xml_data) != 1:
            raise ValueError("There must be one root element")

        tag_name, data = next(iter(xml_data.items()))
        fragment = cls._fragment(tag_name, **data)

        return ElementTree(fragment)

    @classmethod
    def fragment(cls, xml_data):
        return cls.tree(xml_data).getroot()

    @classmethod
    def _fragment(cls, tag_name, _attrs=None, **children):
        return cls._fill_out(Element(tag_name), _attrs, **children)

    @classmethod
    def _sub_element(cls, parent, tag_name, _attrs=None, **children):
        return cls._fill_out(SubElement(parent, tag_name), _attrs, **children)

    @classmethod
    def _fill_out(cls, node, _attrs=None, **children):
        if _attrs:
            node.attrib = _attrs

        if children:
            for tag_name, data in children.items():

                if isinstance(data, dict):
                    cls._sub_element(node, tag_name, **data)
                else:
                    SubElement(node, tag_name).text = str(data)

        return node
