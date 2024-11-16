from io import BytesIO, BufferedReader
from enum import Enum
import sys
import zlib

def reduce_size(file, fixZ2 = False):
    for i in file:
        with open(i, mode="rb") as rsc:
            if rsc.read(4) != b"\x52\x53\x43\x05":
                print("File ", i, "not a wdr or wft file!")
                continue

            version = rsc.read(4)
            flag = rsc.read(4)

            system_size = (bin_to_int(flag) & 0x7FF) << (((bin_to_int(flag) >> 11) & 0xF) + 8)

            content = BytesIO(zlib.decompress(rsc.read()))

            vft = content.read(4)

            if vft == b"\x54\x52\x69\x00" or vft == b"\x0d\xf6\xaa\xb8":
                rsc = b"\x52\x53\x43\x05" + version + flag + zlib.compress(del_useless_data(content, system_size, fixZ2 = fixZ2), 9)

                with open(i, mode="wb") as rsc_to_write:
                    rsc_to_write.write(rsc)

            elif vft == b"\x38\x52\x69\x00" or vft == b"\x09\x46\x0a\x93":
                rsc = b"\x52\x53\x43\x05" + version + flag + zlib.compress(del_useless_data(content, system_size, True, fixZ2), 9)

                with open(i, mode="wb") as rsc_to_write:
                    rsc_to_write.write(rsc)

            else:
                print("file ", i, "not a wdr or wft file!")
                continue

def del_useless_data(content: BufferedReader, system_size:int, is_frag = False, fixZ2 = False):
    content.seek(0)
    content_bytes = bytearray(content.read())

    if is_frag:
        drawable_pointers = []

        if fixZ2:
            content_bytes[0 : 4] = bytearray(b"\x38\x52\x69\x00")

        content.seek(180)
        drawable_pointers.append(bin_pointer_to_int(content.read(4)))

        content.seek(212)
        child_collection_pointer = bin_pointer_to_int(content.read(4))

        if child_collection_pointer != b"\x00\x00\x00\x00":
            content.seek(499)
            child_count = bin_to_int(content.read(1))

            content.seek(child_collection_pointer)
            child_pointers = []

            for i in range(child_count):
                child_pointers.append(bin_pointer_to_int(content.read(4)))

            for child_pointer in child_pointers:
                content.seek(child_pointer + 144)
                drawable_pointers.append(bin_pointer_to_int(content.read(4)))

            model_collections_pointers = []

            for drawable_pointer in drawable_pointers:
                model_collections_pointers.append(drawable_pointer + 64)

    else:
        if fixZ2:
            content_bytes[0 : 4] = bytearray(b"\x54\x52\x69\x00")

        model_collections_pointers = [64]

    for model_collections_pointer in model_collections_pointers:
        for i in range(4):
            content.seek(model_collections_pointer + i * 4)
            model_pointer = content.read(4)

            if model_pointer != b"\x00\x00\x00\x00":
                model_pointer = bin_pointer_to_int(model_pointer)

                content.seek(model_pointer)
                model_collection_pointer = bin_pointer_to_int(content.read(4))
                models_count = bin_to_int(content.read(2))

                for i in range(models_count):
                    content.seek(model_collection_pointer + i * 4)

                    model_pointer = bin_pointer_to_int(content.read(4))
                    content.seek(model_pointer + 4)

                    geometries_collection_pointer = bin_pointer_to_int(content.read(4))
                    geometries_count = bin_to_int(content.read(2))

                    for i in range(geometries_count):
                        content.seek(geometries_collection_pointer + i * 4)

                        geometry_pointer = bin_pointer_to_int(content.read(4))
                        content.seek(geometry_pointer + 12)

                        vertex_buffer_pointer = bin_pointer_to_int(content.read(4))
                        content.seek(vertex_buffer_pointer + 4)

                        vertex_count = bin_to_int(content.read(2))
                        content.seek(vertex_buffer_pointer + 12)

                        stride_size = bin_to_int(content.read(4))

                        vertex_decl_pointer = bin_pointer_to_int(content.read(4))

                        content.seek(vertex_buffer_pointer + 24)
                        vertex_data_pointer = content.read(4)

                        if fixZ2:
                            content_bytes[vertex_buffer_pointer + 8 : vertex_buffer_pointer + 12] = bytearray(vertex_data_pointer)

                        vertex_data_pointer = bin_pointer_to_int(vertex_data_pointer)
                        
                        content.seek(vertex_decl_pointer)

                        vertex_elements_flags =  bin_to_int(content.read(4))
                        #print(hex(vertex_elements_flags))
                        content.read(3)

                        vertex_decl = bin_to_int(content.read(8))

                        vertex_elements = []

                        for i in range(16):
                            if (vertex_elements_flags & (1 << i)) != 0:
                                vertex_elements.append((VertexElementUsage(i), VertexElementFormat[VertexElementUsage(i).name].value))

                        vertex_offset = 0
                        vertex_normal_offset = None
                        vertex_tangent_offset = None
                        vertex_binormal_offset = None

                        for e in vertex_elements:
                            if e[0] == VertexElementUsage.normal:
                                vertex_normal_offset = vertex_offset
                                vertex_normal_all_offset = vertex_data_pointer + system_size + vertex_normal_offset

                            if e[0] == VertexElementUsage.tangent:
                                vertex_tangent_offset = vertex_offset
                                vertex_tangent_all_offset = vertex_data_pointer + system_size + vertex_tangent_offset

                            if e[0] == VertexElementUsage.binormal:
                                vertex_binormal_offset = vertex_offset
                                vertex_binormal_all_offset = vertex_data_pointer + system_size + vertex_binormal_offset
                            
                            vertex_offset += e[1][0] * e[1][1]

                        #content.seek(vertex_data_pointer)
                        #vertex_data = content.read(vertex_count * stride_size)

                        for i in range(int(vertex_count)):
                            if vertex_normal_offset != None:
                                for c in range(3):
                                    content_bytes[vertex_normal_all_offset + i * stride_size + c * 4 : vertex_normal_all_offset + i * stride_size + c * 4 + 2] = bytearray(b"\x00\x00")

                            if vertex_tangent_offset != None:
                                for c in range(4):
                                    content_bytes[vertex_tangent_all_offset + i * stride_size + c * 4 : vertex_tangent_all_offset + i * stride_size + c * 4 + 2] = bytearray(b"\x00\x00")

                            if vertex_binormal_offset != None:
                                for c in range(4):
                                    content_bytes[vertex_binormal_all_offset + i * stride_size + c * 4 : vertex_binormal_all_offset + i * stride_size + c * 4 + 2] = bytearray(b"\x00\x00")
                            #print(struct.unpack("f",content_bytes[vertex_data_pointer + system_size + i * stride_size + stride_size - 8 : vertex_data_pointer + system_size + i * stride_size + stride_size - 4])[0])
                            #print(struct.unpack("f",content_bytes[vertex_data_pointer + system_size + i * stride_size + stride_size - 4 : vertex_data_pointer + system_size + i * stride_size + stride_size])[0])
                            ##print(content_bytes[vertex_data_pointer + system_size + i * stride_size + 12 : vertex_data_pointer + system_size + i * stride_size + 14])
                            ##print(content_bytes[vertex_data_pointer + system_size + i * stride_size + 16 : vertex_data_pointer + system_size + i * stride_size + 18])
                            ##print(content_bytes[vertex_data_pointer + system_size + i * stride_size + 20 : vertex_data_pointer + system_size + i * stride_size + 22])

                            #content_bytes[vertex_data_pointer + system_size + i * stride_size + stride_size - 8 : vertex_data_pointer + system_size + i * stride_size + stride_size - 4] = bytearray(b"\x00\x00\x00\x00")
                            #content_bytes[vertex_data_pointer + system_size + i * stride_size + stride_size - 4 : vertex_data_pointer + system_size + i * stride_size + stride_size] = bytearray(b"\x00\x00\x00\x00")

                            #content_bytes[vertex_data_pointer + system_size + i * stride_size + 12 : vertex_data_pointer + system_size + i * stride_size + 14] = bytearray(b"\x00\x00")
                            #content_bytes[vertex_data_pointer + system_size + i * stride_size + 16 : vertex_data_pointer + system_size + i * stride_size + 18] = bytearray(b"\x00\x00")
                            #content_bytes[vertex_data_pointer + system_size + i * stride_size + 20 : vertex_data_pointer + system_size + i * stride_size + 22] = bytearray(b"\x00\x00")

    return bytes(content_bytes)

class VertexElementUsage(Enum):
    position = 0
    blendweights = 1
    blendindices = 2
    normal = 3
    colour0 = 4
    colour1 = 5
    texcoord0 = 6
    texcoord1 = 7
    texcoord2 = 8
    texcoord3 = 9
    texcoord4 = 10
    texcoord5 = 11
    texcoord6 = 12
    texcoord7 = 13
    tangent = 14
    binormal = 15

class VertexElementFormat(Enum):
    position = (3, 4)
    blendweights = (4, 1)
    blendindices = (4, 1)
    normal = (3, 4)
    colour0 = (4, 1)
    colour1 = (4, 1)
    texcoord0 = (2, 4)
    texcoord1 = (2, 4)
    texcoord2 = (2, 4)
    texcoord3 = (2, 4)
    texcoord4 = (2, 4)
    texcoord5 = (2, 4)
    texcoord6 = (2, 4)
    texcoord7 = (2, 4)
    tangent = (4, 4)
    binormal = (4, 4)

def bin_pointer_to_int(data:bytes):
    data = bytearray(data)
    data[3] = bytearray(b"\x00")[0]
    data = bytes(data)
    return int.from_bytes(data,"little")

def bin_to_int(data:bytes):
    return int.from_bytes(data,"little")

if __name__ == "__main__":
    reduce_size(sys.argv[1 :])